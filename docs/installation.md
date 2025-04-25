# 安装指南

## 系统要求

- Python 3.7+（使用py文件运行必选）
- Git (已安装并配置)

---

## 安装步骤

##从已编译运行

下载已发布的EXE文件

运行！

##从源码运行

### 1. 克隆仓库

```bash
git clone https://github.com/yourusername/mgit.git
cd mgit
```

### 2. 创建虚拟环境 (推荐)

#### Windows:

```cmd
python -m venv venv
venv\Scripts\activate
```

#### macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 运行应用

```bash
python run.py
```

## 可能遇到的问题

### PyQt-Fluent-Widgets 安装问题

如果在安装 PyQt-Fluent-Widgets 时遇到问题，请尝试先安装其依赖:

```bash
pip install PyQt5
```

### Git 配置问题

确保您已经在全局范围内配置了 Git 用户名和邮箱:

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

## 更新应用

当有新版本发布时，运行以下命令获取最新版本:

```bash
git pull
pip install -r requirements.txt
``` 

##自行编译

### 1. 克隆仓库

```bash
git clone https://github.com/yourusername/mgit.git
cd mgit
```

### 2. 创建虚拟环境 (推荐)

#### Windows:

```cmd
python -m venv venv
venv\Scripts\activate
```

#### macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 编辑psy
