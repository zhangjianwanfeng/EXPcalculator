# Google Sheets设置指南

## 1. 创建Google Sheets

1. 访问 https://sheets.google.com
2. 创建新的电子表格
3. 重命名第一个工作表为"访问记录"
4. 设置标题行：
   - A1: 时间戳
   - B1: IP地址  
   - C1: User-Agent
   - D1: 额外信息

## 2. 获取电子表格ID

从URL中复制ID：
https://docs.google.com/spreadsheets/d/YOUR_SPREADSHEET_ID/edit

## 3. 设置Google Cloud项目

1. 访问 https://console.cloud.google.com
2. 创建新项目或选择现有项目
3. 启用Google Sheets API
4. 创建服务账号
5. 下载JSON密钥文件

## 4. 配置凭据

将下载的JSON文件重命名为credentials.json并放在项目根目录

## 5. 设置权限

在Google Sheets中，将服务账号邮箱添加为编辑者

## 6. 环境变量（生产环境）

在Vercel等平台设置以下环境变量：
- GOOGLE_CREDENTIALS_JSON: 服务账号JSON内容
- GOOGLE_SHEETS_ID: 电子表格ID
