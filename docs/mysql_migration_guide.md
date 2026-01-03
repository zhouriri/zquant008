# MySQL 5.6.29 → 8.4.7 迁移指南

## 概述

本文档详细说明如何将 ZQuant 项目的数据库从 MySQL 5.6.29 迁移到 MySQL 8.4.7。

## 迁移前准备

### 1. 系统要求

- **源数据库**: MySQL 5.6.29
- **目标数据库**: MySQL 8.4.7
- **操作系统**: Windows / Linux / macOS
- **Python**: 3.8+
- **必需工具**: mysqldump, mysql, mysql_upgrade

### 2. 备份策略

**重要**: 迁移前必须完整备份所有数据！

```bash
# 备份所有数据库
mysqldump -u root -p --all-databases --routines --triggers --events > full_backup.sql

# 备份特定数据库
mysqldump -u root -p --databases zquant --routines --triggers --events > zquant_backup.sql

# 备份用户和权限
mysqldump -u root -p mysql user db tables_priv columns_priv > mysql_users_backup.sql
```

### 3. 检查清单

- [ ] 已备份所有数据
- [ ] 已备份用户和权限
- [ ] 已检查磁盘空间（至少是数据库大小的2倍）
- [ ] 已通知相关人员迁移计划
- [ ] 已准备回滚方案

## 迁移步骤

### 方法一：使用自动迁移脚本（推荐）

#### 1. 安装 MySQL 8.4.7

**Windows:**
1. 下载 MySQL 8.4.7 安装包
2. 运行安装程序
3. 选择"仅服务器"或"完整安装"
4. 配置端口（建议使用3307，避免与5.6冲突）

**Linux:**
```bash
# Ubuntu/Debian
wget https://dev.mysql.com/get/mysql-apt-config_0.8.xx-1_all.deb
sudo dpkg -i mysql-apt-config_0.8.xx-1_all.deb
sudo apt-get update
sudo apt-get install mysql-server

# CentOS/RHEL
sudo yum install mysql-server
```

#### 2. 配置 MySQL 8.4.7

复制配置文件模板：
```bash
# Linux
sudo cp docker/mysql8.4.cnf /etc/mysql/my.cnf

# Windows
# 复制 docker/mysql8.4.cnf 到 MySQL 安装目录的 my.ini
```

**关键配置说明：**
- `default-authentication-plugin = mysql_native_password`: 兼容旧客户端
- `sql_mode`: 设置兼容的SQL模式
- `character-set-server = utf8mb4`: 使用UTF8MB4字符集

#### 3. 启动 MySQL 8.4.7

```bash
# Linux
sudo systemctl start mysql

# Windows
net start MySQL80
```

#### 4. 运行迁移脚本

```bash
# 基本用法
python zquant/scripts/migrate_mysql_5.6_to_8.4.py \
    --source-host localhost \
    --source-port 3307 \
    --source-user root \
    --source-password your_password \
    --source-database zquant \
    --target-host localhost \
    --target-port 3306 \
    --target-user root \
    --target-password your_password \
    --target-database zquant \
    --backup-dir backups
```

**参数说明：**
- `--source-*`: 源数据库（MySQL 5.6）连接信息
- `--target-*`: 目标数据库（MySQL 8.4）连接信息
- `--backup-dir`: 备份文件保存目录

#### 5. 验证迁移结果

脚本会自动验证：
- 数据库版本
- 表数量
- 表记录数（估算值）

手动验证：
```sql
-- 连接目标数据库
mysql -u root -p -h localhost -P 3307

-- 检查数据库
SHOW DATABASES;
USE zquant;
SHOW TABLES;

-- 检查数据量
SELECT COUNT(*) FROM your_table;

-- 检查字符集
SHOW CREATE TABLE your_table;

-- 检查MySQL版本
SELECT VERSION();
```

### 方法二：手动迁移

#### 1. 备份源数据库

```bash
mysqldump -u root -p \
    --databases zquant \
    --routines \
    --triggers \
    --events \
    --single-transaction \
    --quick \
    --lock-tables=false \
    > zquant_backup.sql
```

#### 2. 创建目标数据库

```sql
CREATE DATABASE zquant CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

#### 3. 恢复数据

```bash
mysql -u root -p -h localhost -P 3307 zquant < zquant_backup.sql
```

#### 4. 运行升级工具

```bash
mysql_upgrade -u root -p -h localhost -P 3307
```

#### 5. 更新用户认证方式

```sql
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'your_password';
ALTER USER 'root'@'%' IDENTIFIED WITH mysql_native_password BY 'your_password';
FLUSH PRIVILEGES;
```

## 迁移后处理

### 1. 更新应用程序配置

检查 `.env` 文件，确保数据库连接信息正确：

```env
DB_HOST=localhost
DB_PORT=3307  # 如果MySQL 8.4使用不同端口
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=zquant
DB_CHARSET=utf8mb4
```

### 2. 测试应用程序

1. **测试数据库连接**
   ```bash
   python -c "from zquant.database import engine; engine.connect()"
   ```

2. **测试基本功能**
   - 用户登录
   - 数据查询
   - 数据写入
   - 复杂查询（特别是窗口函数）

3. **性能测试**
   - 查询响应时间
   - 并发连接
   - 大数据量查询

### 3. 优化配置

根据实际使用情况调整 MySQL 8.4 配置：

```ini
# 根据服务器内存调整
innodb_buffer_pool_size = 2G  # 建议设置为物理内存的50-70%

# 根据并发连接数调整
max_connections = 500
```

## 常见问题

### 问题1：密码认证失败

**错误**: `Authentication plugin 'caching_sha2_password' cannot be loaded`

**解决方案**:
```sql
ALTER USER 'username'@'host' IDENTIFIED WITH mysql_native_password BY 'password';
FLUSH PRIVILEGES;
```

### 问题2：字符集问题

**错误**: 中文乱码

**解决方案**:
```sql
-- 转换表字符集
ALTER TABLE table_name CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 转换数据库字符集
ALTER DATABASE zquant CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 问题3：SQL模式差异

**错误**: SQL语法错误

**解决方案**:
```sql
-- 查看当前SQL模式
SELECT @@sql_mode;

-- 设置兼容模式
SET sql_mode = 'STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';
```

### 问题4：窗口函数不支持

**错误**: `You have an error in your SQL syntax`

**解决方案**: MySQL 8.0+ 支持窗口函数，如果出现错误，检查：
1. MySQL版本是否 >= 8.0
2. SQL语法是否正确
3. 是否有语法冲突

## 回滚方案

如果迁移失败，可以回滚：

1. **停止 MySQL 8.4**
   ```bash
   sudo systemctl stop mysql  # Linux
   net stop MySQL80           # Windows
   ```

2. **恢复备份**
   ```bash
   mysql -u root -p < zquant_backup.sql
   ```

3. **重新启动 MySQL 5.6**
   ```bash
   sudo systemctl start mysql56  # Linux
   net start MySQL56              # Windows
   ```

## 性能对比

MySQL 8.4 相比 5.6 的性能提升：

- **查询性能**: 提升 20-50%（取决于查询类型）
- **并发处理**: 更好的多线程处理
- **JSON支持**: 原生JSON数据类型和函数
- **窗口函数**: 支持窗口函数，简化复杂查询
- **CTE支持**: 支持公共表表达式（CTE）

## 注意事项

1. **备份**: 迁移前必须完整备份
2. **测试**: 在测试环境先验证
3. **停机时间**: 计划适当的维护窗口
4. **监控**: 迁移后密切监控系统性能
5. **文档**: 记录迁移过程和遇到的问题

## 参考资源

- [MySQL 8.4 官方文档](https://dev.mysql.com/doc/refman/8.4/en/)
- [MySQL 升级指南](https://dev.mysql.com/doc/refman/8.4/en/upgrading.html)
- [MySQL 兼容性说明](https://dev.mysql.com/doc/refman/8.4/en/mysql-nutshell.html)

## 支持

如遇到问题，请：
1. 查看日志文件：`logs/zquant.log`
2. 检查 MySQL 错误日志
3. 联系技术支持团队
