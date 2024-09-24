import uuid as py_uuid
from typing import Any, Dict, List, Optional

from sqlalchemy import ARRAY, JSON, BigInteger, DateTime, Float, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class SKU(Base):
    __tablename__ = "sku"

    uuid: Mapped[py_uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=py_uuid.uuid4,
        unique=True,
        comment="id товара в нашей бд",
    )
    marketplace_id: Mapped[Optional[int]] = mapped_column(
        Integer, comment="id маркетплейса"
    )
    product_id: Mapped[int] = mapped_column(
        BigInteger, nullable=False, comment="id товара в маркетплейсе"
    )
    title: Mapped[Optional[str]] = mapped_column(Text, comment="название товара")
    description: Mapped[Optional[str]] = mapped_column(Text, comment="описание товара")
    brand: Mapped[Optional[str]] = mapped_column(
        Text, index=True, comment="Бренд товара"
    )
    seller_id: Mapped[Optional[int]] = mapped_column(Integer, comment="ID продавца")
    seller_name: Mapped[Optional[str]] = mapped_column(
        Text, comment="Название продавца"
    )
    first_image_url: Mapped[Optional[str]] = mapped_column(
        Text, comment="URL первой картинки товара"
    )
    category_id: Mapped[Optional[int]] = mapped_column(
        Integer, comment="ID категории товара"
    )
    category_lvl_1: Mapped[Optional[str]] = mapped_column(
        Text, comment="Первая часть категории товара"
    )
    category_lvl_2: Mapped[Optional[str]] = mapped_column(
        Text, comment="Вторая часть категории товара"
    )
    category_lvl_3: Mapped[Optional[str]] = mapped_column(
        Text, comment="Третья часть категории товара"
    )
    category_remaining: Mapped[Optional[str]] = mapped_column(
        Text, comment="Остаток категории товара"
    )
    features: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, comment="Характеристики товара"
    )
    rating_count: Mapped[Optional[int]] = mapped_column(
        Integer, comment="Кол-во отзывов о товаре"
    )
    rating_value: Mapped[Optional[float]] = mapped_column(
        Float, comment="Рейтинг товара (0-5)"
    )
    price_before_discounts: Mapped[Optional[float]] = mapped_column(
        Float, comment="Цена до скидок"
    )
    discount: Mapped[Optional[float]] = mapped_column(Float, comment="Скидка")
    price_after_discounts: Mapped[Optional[float]] = mapped_column(
        Float, comment="Цена после скидок"
    )
    bonuses: Mapped[Optional[int]] = mapped_column(Integer, comment="Бонусы")
    sales: Mapped[Optional[int]] = mapped_column(Integer, comment="Продажи")
    inserted_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        comment="Дата вставки записи",
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="Дата обновления записи",
    )
    currency: Mapped[Optional[str]] = mapped_column(Text, comment="Валюта")
    barcode: Mapped[Optional[str]] = mapped_column(Text, comment="Штрихкод")
    similar_sku: Mapped[Optional[List[py_uuid.UUID]]] = mapped_column(
        ARRAY(UUID(as_uuid=True)),
        comment="Похожие товары",
    )
