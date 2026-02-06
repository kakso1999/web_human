"""
Payment 模块 - API 路由
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from core.middleware.auth import get_current_user_id
from core.schemas.base import success_response
from core.config.settings import get_settings
from .schemas import CreateOrderRequest, CaptureOrderRequest, PLAN_PRICES
from .service import get_paypal_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/payment", tags=["Payment"])


@router.get("/config", summary="获取支付配置")
async def get_payment_config():
    """
    获取前端需要的支付配置
    - PayPal Client ID
    - 价格信息
    """
    settings = get_settings()
    return success_response({
        "paypal_client_id": settings.PAYPAL_CLIENT_ID,
        "paypal_mode": settings.PAYPAL_MODE,
        "plans": {
            "basic": {
                "price": PLAN_PRICES["basic"],
                "currency": "USD",
                "features": [
                    "20 voice profiles",
                    "10 avatar profiles",
                    "50 story generations/month",
                    "Unlimited audiobooks",
                    "Priority processing"
                ]
            },
            "premium": {
                "price": PLAN_PRICES["premium"],
                "currency": "USD",
                "features": [
                    "Unlimited voice profiles",
                    "Unlimited avatar profiles",
                    "Unlimited story generations",
                    "Unlimited audiobooks",
                    "Priority processing",
                    "HD video export (1080p)"
                ]
            }
        }
    })


@router.post("/orders", summary="创建支付订单")
async def create_order(
    request: CreateOrderRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    创建 PayPal 支付订单

    返回订单 ID 和支付页面 URL
    """
    try:
        service = get_paypal_service()
        order_id, approval_url = await service.create_order(
            plan=request.plan,
            user_id=user_id
        )

        return success_response({
            "order_id": order_id,
            "approval_url": approval_url
        })

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to create payment order: {e}")
        raise HTTPException(status_code=500, detail="Failed to create payment order")


@router.post("/orders/{order_id}/capture", summary="完成支付")
async def capture_order(
    order_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    捕获（完成）PayPal 支付

    用户在 PayPal 批准支付后调用此接口完成交易
    """
    try:
        service = get_paypal_service()
        result = await service.capture_order(
            order_id=order_id,
            user_id=user_id
        )

        return success_response(result)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception(f"Failed to capture payment: {e}")
        raise HTTPException(status_code=500, detail="Failed to complete payment")


@router.get("/history", summary="获取支付历史")
async def get_payment_history(
    user_id: str = Depends(get_current_user_id)
):
    """
    获取用户的支付历史记录
    """
    try:
        service = get_paypal_service()
        payments = await service.get_user_payments(user_id)
        return success_response({"payments": payments})
    except Exception as e:
        logger.exception(f"Failed to get payment history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get payment history")
