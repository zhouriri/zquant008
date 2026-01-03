
from sqlalchemy.sql import func
import os

file_path = "zquant/models/data.py"
print(f"Checking {file_path}...")

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

if "class HslChoice(Base):" in content:
    print("HslChoice already exists in the file.")
else:
    new_class_code = """

class HslChoice(Base):
    \"\"\"ZQ精选数据表\"\"\"

    __database__ = "zquant"  # 数据库名称
    __tablename__ = "zq_data_hsl_choice"  # 数据表名称
    __cnname__ = "ZQ精选数据"  # 数据表中文名称
    __datasource__ = "手工录入"  # 数据源

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    trade_date = Column(Date, nullable=False, index=True, info={"name": "交易日期"}, comment="交易日期")
    ts_code = Column(String(20), nullable=False, index=True, info={"name": "TS代码"}, comment="TS代码")
    created_by = Column(String(50), nullable=True, info={"name": "创建人"}, comment="创建人")
    created_time = Column(DateTime, default=func.now(), nullable=False, info={"name": "创建时间"}, comment="创建时间")
    updated_by = Column(String(50), nullable=True, info={"name": "修改人"}, comment="修改人")
    updated_time = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False, info={"name": "修改时间"}, comment="修改时间"
    )

    # 唯一约束：同一交易日期同一股票只能有一条记录
    __table_args__ = (
        UniqueConstraint("trade_date", "ts_code", name="uq_hsl_choice_date_code"),
    )

    class Config:
        from_attributes = True
"""
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(new_class_code)
    print("Successfully appended HslChoice class to data.py.")
