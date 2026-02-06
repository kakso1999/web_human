"""
Payment 模块 - Schema 定义
"""
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field


class CreateOrderRequest(BaseModel):
    """创建订单请求"""
    plan: Literal["basic", "premium"] = Field(..., description="订阅计划")


class CreateOrderResponse(BaseModel):
    """创建订单响应"""
    order_id: str = Field(..., description="PayPal 订单 ID")
    approval_url: str = Field(..., description="PayPal 支付页面 URL")


class CaptureOrderRequest(BaseModel):
    """捕获订单请求"""
    order_id: str = Field(..., description="PayPal 订单 ID")


class PaymentRecord(BaseModel):
    """支付记录"""
    id: str = Field(..., description="记录 ID")
    user_id: str = Field(..., description="用户 ID")
    order_id: str = Field(..., description="PayPal 订单 ID")
    plan: str = Field(..., description="订阅计划")
    amount: float = Field(..., description="支付金额")
    currency: str = Field(default="USD", description="货币")
    status: str = Field(..., description="支付状态")
    payer_email: Optional[str] = Field(None, description="付款人邮箱")
    created_at: datetime = Field(..., description="创建时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")


class SubscriptionInfo(BaseModel):
    """订阅信息"""
    plan: str = Field(..., description="当前计划")
    expires_at: Optional[datetime] = Field(None, description="到期时间")
    is_active: bool = Field(..., description="是否有效")


# 订阅计划价格配置
PLAN_PRICES = {
    "basic": 9.90,
    "premium": 19.90
}

# 订阅时长（天）
SUBSCRIPTION_DAYS = 30
