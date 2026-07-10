## 架构
![[Pasted image 20260708211810.png]]
可以看到， MySQL 的架构共分为两层：**Server 层和存储引擎层**
MySQL服务器管理多个**数据库**（Database），每个数据库中包含若干个**表**（table），

## 查询
### 基础查询
增删改查：insert/delete/update/select
### 多表查询
1. 内连接：$A\cap B$
2. 外连接：$A + A \cap B$
3. 自连接：将一张表看作两张表，A as a, b，语法与内连接、外连接相同
