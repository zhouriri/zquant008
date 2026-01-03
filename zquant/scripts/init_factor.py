# Copyright 2025 ZQuant Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the Apache License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Author: kevin
# Contact:
#     - Email: kevin@vip.qq.com
#     - Wechat: zquant2025
#     - Issues: https://github.com/yoyoung/zquant/issues
#     - Documentation: https://github.com/yoyoung/zquant/blob/main/README.md
#     - Repository: https://github.com/yoyoung/zquant

"""
因子系统初始化脚本

功能：
1. 创建因子相关表（包括新的FactorConfig表，以factor_id为主键）
2. 初始化换手率因子定义和模型
3. 创建示例因子配置（使用新的FactorConfig表）
4. 支持从FactorDefinition.factor_config_json迁移数据到新表

注意：
- FactorConfig表以factor_id为主键，每个因子对应一条配置记录
- 配置以JSON格式存储在config_json字段中
"""

import argparse
import sys
from pathlib import Path

# 添加项目根目录到路径
script_dir = Path(__file__).resolve().parent  # zquant/scripts
zquant_dir = script_dir.parent  # zquant 目录
project_root = zquant_dir.parent  # 项目根目录（包含 zquant 目录的目录）
sys.path.insert(0, str(project_root))

from loguru import logger
from sqlalchemy import text
from sqlalchemy.orm import Session

from zquant.database import SessionLocal, engine
from zquant.models.factor import FactorConfig, FactorDefinition, FactorModel, FACTOR_TYPE_COMBINED, FACTOR_TYPE_SINGLE
from zquant.services.factor import FactorService


def create_tables():
    """创建因子相关表"""
    logger.info("开始创建因子相关数据库表...")
    try:
        with engine.begin() as conn:  # 使用 begin() 自动管理事务
            # 创建因子定义表
            conn.execute(
                text("""
                CREATE TABLE IF NOT EXISTS zq_quant_factor_definitions (
                    id INTEGER AUTO_INCREMENT PRIMARY KEY,
                    factor_name VARCHAR(100) NOT NULL UNIQUE,
                    cn_name VARCHAR(100) NOT NULL,
                    en_name VARCHAR(100),
                    column_name VARCHAR(100) NOT NULL,
                    description TEXT,
                    factor_type VARCHAR(20) DEFAULT '单因子' COMMENT '因子类型：单因子、组合因子',
                    enabled BOOLEAN NOT NULL DEFAULT TRUE,
                    created_by VARCHAR(50) COMMENT '创建人',
                    created_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_by VARCHAR(50) COMMENT '修改人',
                    updated_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_factor_name (factor_name),
                    INDEX idx_enabled (enabled),
                    INDEX idx_factor_type (factor_type)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
            )

            # 创建因子模型表
            conn.execute(
                text("""
                CREATE TABLE IF NOT EXISTS zq_quant_factor_models (
                    id INTEGER AUTO_INCREMENT PRIMARY KEY,
                    factor_id INTEGER NOT NULL,
                    model_name VARCHAR(100) NOT NULL,
                    model_code VARCHAR(50) NOT NULL,
                    config_json TEXT,
                    is_default BOOLEAN NOT NULL DEFAULT FALSE,
                    enabled BOOLEAN NOT NULL DEFAULT TRUE,
                    created_by VARCHAR(50) COMMENT '创建人',
                    created_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_by VARCHAR(50) COMMENT '修改人',
                    updated_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_factor_id (factor_id),
                    INDEX idx_model_code (model_code),
                    INDEX idx_is_default (is_default),
                    INDEX idx_enabled (enabled),
                    FOREIGN KEY (factor_id) REFERENCES zq_quant_factor_definitions(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
            )

            # 创建因子配置表（以factor_id为主键）
            conn.execute(
                text("""
                CREATE TABLE IF NOT EXISTS zq_quant_factor_configs (
                    factor_id INTEGER NOT NULL PRIMARY KEY,
                    config_json TEXT COMMENT '因子配置（JSON格式）：{"enabled": true, "mappings": [{"model_id": 1, "codes": [...]}]}',
                    enabled BOOLEAN NOT NULL DEFAULT TRUE,
                    created_by VARCHAR(50) COMMENT '创建人',
                    created_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_by VARCHAR(50) COMMENT '修改人',
                    updated_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_factor_id (factor_id),
                    INDEX idx_enabled (enabled),
                    FOREIGN KEY (factor_id) REFERENCES zq_quant_factor_definitions(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)
            )

            # 使用 engine.begin() 时，事务会在 with 块结束时自动提交
            logger.info("因子相关表创建完成")
            return True
    except Exception as e:
        logger.error(f"创建因子相关表失败: {e}")
        return False


def create_turnover_rate_factor(force: bool = False):
    """创建换手率因子定义和模型"""
    logger.info("开始创建换手率因子...")

    db = SessionLocal()
    try:
        # 检查是否已存在
        factor_def = FactorService.get_factor_definition_by_name(db, "turnover_rate")
        
        if factor_def and not force:
            logger.info("换手率因子定义已存在，检查模型和配置...")
            # 获取默认模型和MA模型
            default_model = db.query(FactorModel).filter(
                FactorModel.factor_id == factor_def.id, 
                FactorModel.model_code == "turnover_rate"
            ).first()
            ma_model = db.query(FactorModel).filter(
                FactorModel.factor_id == factor_def.id, 
                FactorModel.model_code == "turnover_rate_ma"
            ).first()
            
            if not default_model or not ma_model:
                logger.warning("换手率因子模型不完整，请使用 --force 强制重新创建")
                return True
        else:
            # 如果存在且需要强制重新创建，先删除
            if factor_def and force:
                logger.info("删除已存在的换手率因子...")
                FactorService.delete_factor_definition(db, factor_def.id)

            # 创建因子定义
            factor_def = FactorService.create_factor_definition(
                db=db,
                factor_name="turnover_rate",
                cn_name="换手率因子",
                en_name="Turnover Rate",
                column_name="turnover_rate",
                description="换手率因子，反映股票交易的活跃程度",
                factor_type=FACTOR_TYPE_SINGLE,
                enabled=True,
                created_by="admin",
            )

            # 创建默认模型
            default_model = FactorService.create_factor_model(
                db=db,
                factor_id=factor_def.id,
                model_name="换手率因子计算模型（每日指标）",
                model_code="turnover_rate",
                config_json={"source": "daily_basic", "field": "turnover_rate"},
                is_default=True,
                enabled=True,
                created_by="admin",
            )

            # 创建第二个换手率模型（移动平均）
            ma_model = FactorService.create_factor_model(
                db=db,
                factor_id=factor_def.id,
                model_name="换手率因子计算模型（移动平均）",
                model_code="turnover_rate_ma",
                config_json={"source": "daily_basic", "field": "turnover_rate", "method": "ma", "window": 5},
                is_default=False,
                enabled=True,
                created_by="admin",
            )

        # 3. 创建换手率因子配置
        # 直接查询数据库检查是否已存在配置，避免 get_factor_config_by_factor_id 抛出 NotFoundError
        existing_config = db.query(FactorConfig).filter(FactorConfig.factor_id == factor_def.id).first()
        if existing_config:
            if force:
                logger.info("删除已存在的换手率因子配置...")
                FactorService.delete_factor_config_by_factor_id(db, factor_def.id)
            else:
                logger.info("换手率因子配置已存在，跳过创建")
                return True

        # 创建多映射配置
        mappings = [
            {
                "model_id": default_model.id,
                "codes": None,  # 默认配置，用于所有未指定的股票
            },
            {
                "model_id": ma_model.id,
                "codes": ["000001.SZ", "000002.SZ"],  # 特定股票使用移动平均模型示例
            }
        ]

        factor_config = {
            "enabled": True,
            "mappings": mappings,
        }
        
        FactorService.create_factor_config(
            db=db,
            factor_id=factor_def.id,
            config=factor_config,
            created_by="admin",
        )

        logger.info(f"成功创建换手率因子（共 {len(mappings)} 个映射）: factor_id={factor_def.id}, default_model_id={default_model.id}, ma_model_id={ma_model.id}")
        return True

    except Exception as e:
        logger.error(f"创建换手率因子失败: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="因子系统初始化脚本")
    parser.add_argument("--force", action="store_true", help="强制重新创建（删除已存在的记录）")
    parser.add_argument("--tables-only", action="store_true", help="只创建表，不创建示例数据")
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("因子系统初始化开始")
    logger.info("=" * 60)

    # 1. 创建表
    if not create_tables():
        logger.error("创建表失败，退出")
        sys.exit(1)

    if args.tables_only:
        logger.info("只创建表模式，跳过示例数据创建")
        logger.info("=" * 60)
        logger.info("因子系统初始化完成（仅创建表）")
        logger.info("=" * 60)
        return

    # 2. 创建换手率因子 (含配置)
    if not create_turnover_rate_factor(force=args.force):
        logger.error("创建换手率因子失败")
        sys.exit(1)

    # 3. 创建超活跃组合因子
    if not create_hyper_activity_factor(force=args.force):
        logger.warning("创建超活跃组合因子失败（不影响整体流程）")

    logger.info("=" * 60)
    logger.info("因子系统初始化完成")
    logger.info("=" * 60)


def create_hyper_activity_factor(force: bool = False):
    """创建超活跃组合因子定义和模型"""
    logger.info("开始创建超活跃组合因子...")

    db = SessionLocal()
    try:
        # 检查是否已存在
        factor_def = FactorService.get_factor_definition_by_name(db, "hyper_activity")
        
        if factor_def and not force:
            logger.info("超活跃组合因子定义已存在，检查模型和配置...")
            # 获取默认模型
            default_model = db.query(FactorModel).filter(
                FactorModel.factor_id == factor_def.id, 
                FactorModel.model_code == "hyper_activity"
            ).first()
            
            if not default_model:
                logger.warning("超活跃组合因子模型缺失，请使用 --force 强制重新创建")
                return True
        else:
            # 如果存在且需要强制重新创建，先删除
            if factor_def and force:
                logger.info("删除已存在的超活跃组合因子...")
                FactorService.delete_factor_definition(db, factor_def.id)

            # 创建因子定义
            factor_def = FactorService.create_factor_definition(
                db=db,
                factor_name="hyper_activity",
                cn_name="超活跃组合因子",
                en_name="Hyper Activity Factor",
                column_name="hyper_activity",  # 组合因子不使用单一列名，但需要提供一个默认值
                description="超活跃组合因子，包含换手率因子（5/10/20/30/60/90日均值）、小十字因子（振幅≤3%且涨跌幅≤1%的K线统计）、半年统计因子（半年内活跃次数、半年内换手率次数等）",
                factor_type=FACTOR_TYPE_COMBINED,
                enabled=True,
                created_by="admin",
            )

            # 创建默认模型
            default_model = FactorService.create_factor_model(
                db=db,
                factor_id=factor_def.id,
                model_name="超活跃组合因子计算模型",
                model_code="hyper_activity",
                config_json={},  # 超活跃组合因子当前不需要配置
                is_default=True,
                enabled=True,
                created_by="admin",
            )

        logger.info(f"成功创建超活跃组合因子: factor_id={factor_def.id}, model_id={default_model.id}")

        # 3. 为其创建初始因子配置
        # 直接查询数据库检查是否已存在配置，避免 get_factor_config_by_factor_id 抛出 NotFoundError
        existing_config = db.query(FactorConfig).filter(FactorConfig.factor_id == factor_def.id).first()
        if existing_config:
            if force:
                logger.info("删除已存在的超活跃组合因子配置...")
                FactorService.delete_factor_config_by_factor_id(db, factor_def.id)
            else:
                logger.info("超活跃组合因子配置已存在，跳过创建")
                return True

        # 创建默认配置：映射到默认模型，且开启
        mappings = [
            {
                "model_id": default_model.id,
                "codes": None,  # 默认配置，用于所有股票
            }
        ]
        
        factor_config = {
            "enabled": True,
            "mappings": mappings,
        }
        
        FactorService.create_factor_config(
            db=db,
            factor_id=factor_def.id,
            config=factor_config,
            created_by="admin",
        )

        logger.info(f"成功创建超活跃组合因子（共 {len(mappings)} 个映射）: factor_id={factor_def.id}, model_id={default_model.id}")
        return True

    except Exception as e:
        logger.error(f"创建超活跃组合因子失败: {e}")
        db.rollback()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    main()

