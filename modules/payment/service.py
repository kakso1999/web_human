"""
Payment 模块 - PayPal 服务
"""
import logging
import httpx
from datetime import datetime, timedelta
from typing import Optional, Tuple
from bson import ObjectId
from core.config.settings import get_settings
from core.config.database import Database
from .schemas import PLAN_PRICES, SUBSCRIPTION_DAYS

logger = logging.getLogger(__name__)


class PayPalService:
    """PayPal 支付服务"""

    def __init__(self):
        settings = get_settings()
        self.client_id = settings.PAYPAL_CLIENT_ID
        self.client_secret = settings.PAYPAL_CLIENT_SECRET
        self.mode = settings.PAYPAL_MODE  # sandbox or live
        self.frontend_url = settings.FRONTEND_URL

        if self.mode == "live":
            self.base_url = "https://api-m.paypal.com"
        else:
            self.base_url = "https://api-m.sandbox.paypal.com"

        self._access_token: Optional[str] = None
        self._token_expires: Optional[datetime] = None

    async def _get_access_token(self) -> str:
        """获取 PayPal Access Token"""
        # 检查缓存的 token 是否有效
        if self._access_token and self._token_expires and datetime.now() < self._token_expires:
            return self._access_token

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v1/oauth2/token",
                auth=(self.client_id, self.client_secret),
                data={"grant_type": "client_credentials"},
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

            if response.status_code != 200:
                logger.error(f"Failed to get PayPal access token: {response.text}")
                raise Exception("Failed to authenticate with PayPal")

            data = response.json()
            self._access_token = data["access_token"]
            # Token 通常有效期为 9 小时，我们设置 8 小时后过期
            self._token_expires = datetime.now() + timedelta(hours=8)
            return self._access_token

    async def create_order(self, plan: str, user_id: str) -> Tuple[str, str]:
        """
        创建 PayPal 订单

        Args:
            plan: 订阅计划 (basic/premium)
            user_id: 用户 ID

        Returns:
            Tuple[order_id, approval_url]
        """
        if plan not in PLAN_PRICES:
            raise ValueError(f"Invalid plan: {plan}")

        amount = PLAN_PRICES[plan]
        token = await self._get_access_token()

        order_data = {
            "intent": "CAPTURE",
            "purchase_units": [{
                "reference_id": f"{user_id}_{plan}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "description": f"Echobot {plan.capitalize()} Plan - Monthly Subscription",
                "amount": {
                    "currency_code": "USD",
                    "value": f"{amount:.2f}"
                }
            }],
            "application_context": {
                "brand_name": "Echobot",
                "landing_page": "NO_PREFERENCE",
                "user_action": "PAY_NOW",
                "return_url": f"{self.frontend_url}/subscription?success=true",
                "cancel_url": f"{self.frontend_url}/subscription?cancelled=true"
            }
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v2/checkout/orders",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json=order_data
            )

            if response.status_code not in [200, 201]:
                logger.error(f"Failed to create PayPal order: {response.text}")
                raise Exception("Failed to create PayPal order")

            data = response.json()
            order_id = data["id"]

            # 找到 approval URL
            approval_url = None
            for link in data.get("links", []):
                if link["rel"] == "approve":
                    approval_url = link["href"]
                    break

            if not approval_url:
                raise Exception("No approval URL found in PayPal response")

            # 保存订单记录
            db = Database.get_db()
            await db.payment_orders.insert_one({
                "order_id": order_id,
                "user_id": user_id,
                "plan": plan,
                "amount": amount,
                "currency": "USD",
                "status": "CREATED",
                "created_at": datetime.utcnow()
            })

            logger.info(f"Created PayPal order {order_id} for user {user_id}, plan {plan}")
            return order_id, approval_url

    async def capture_order(self, order_id: str, user_id: str) -> dict:
        """
        捕获（完成）PayPal 订单

        Args:
            order_id: PayPal 订单 ID
            user_id: 用户 ID

        Returns:
            支付详情
        """
        # 验证订单属于该用户
        db = Database.get_db()
        order_record = await db.payment_orders.find_one({
            "order_id": order_id,
            "user_id": user_id
        })

        if not order_record:
            raise ValueError("Order not found or does not belong to this user")

        if order_record.get("status") == "COMPLETED":
            raise ValueError("Order already completed")

        token = await self._get_access_token()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v2/checkout/orders/{order_id}/capture",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
            )

            if response.status_code not in [200, 201]:
                logger.error(f"Failed to capture PayPal order: {response.text}")
                raise Exception("Failed to capture payment")

            data = response.json()

            if data.get("status") != "COMPLETED":
                raise Exception(f"Payment not completed, status: {data.get('status')}")

            # 获取付款人信息
            payer_email = None
            if "payer" in data:
                payer_email = data["payer"].get("email_address")

            # 更新订单状态
            await db.payment_orders.update_one(
                {"order_id": order_id},
                {
                    "$set": {
                        "status": "COMPLETED",
                        "payer_email": payer_email,
                        "completed_at": datetime.utcnow(),
                        "paypal_response": data
                    }
                }
            )

            # 更新用户订阅
            plan = order_record["plan"]
            expires_at = datetime.utcnow() + timedelta(days=SUBSCRIPTION_DAYS)

            # user_id 是字符串，需要转换为 ObjectId
            user_oid = ObjectId(order_record["user_id"])
            result = await db.users.update_one(
                {"_id": user_oid},
                {
                    "$set": {
                        "subscription.plan": plan,
                        "subscription.expires_at": expires_at,
                        "subscription.updated_at": datetime.utcnow()
                    }
                }
            )
            logger.info(f"Updated user subscription: matched={result.matched_count}, modified={result.modified_count}")

            logger.info(f"Payment completed for order {order_id}, user {user_id} upgraded to {plan}")

            return {
                "status": "success",
                "plan": plan,
                "expires_at": expires_at.isoformat(),
                "payer_email": payer_email
            }

    async def get_user_payments(self, user_id: str, limit: int = 10) -> list:
        """获取用户支付历史"""
        db = Database.get_db()
        cursor = db.payment_orders.find(
            {"user_id": user_id}
        ).sort("created_at", -1).limit(limit)

        payments = []
        async for doc in cursor:
            payments.append({
                "order_id": doc["order_id"],
                "plan": doc["plan"],
                "amount": doc["amount"],
                "currency": doc["currency"],
                "status": doc["status"],
                "created_at": doc["created_at"].isoformat(),
                "completed_at": doc.get("completed_at", "").isoformat() if doc.get("completed_at") else None
            })

        return payments


# 单例
_paypal_service: Optional[PayPalService] = None


def get_paypal_service() -> PayPalService:
    """获取 PayPal 服务单例"""
    global _paypal_service
    if _paypal_service is None:
        _paypal_service = PayPalService()
    return _paypal_service
