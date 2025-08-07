import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import logging
import os

class GoogleSheetsService:
    def __init__(self, spreadsheet_id=None, worksheet_name=None):
        # 优先使用环境变量，然后使用配置文件，最后使用默认值
        self.spreadsheet_id = spreadsheet_id or os.environ.get('GOOGLE_SHEETS_ID')
        self.worksheet_name = worksheet_name or "Sheet1"  # 使用默认工作表名称
        self.client = None
        self.worksheet = None
        
    def connect(self):
        """连接到Google Sheets"""
        try:
            # 设置API范围
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            
            # 优先尝试从环境变量获取凭据
            credentials_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')
            if credentials_json:
                import json
                try:
                    credentials = Credentials.from_service_account_info(
                        json.loads(credentials_json), scopes=scope
                    )
                    logging.info("使用环境变量中的Google Sheets凭据")
                except json.JSONDecodeError as e:
                    logging.error(f"环境变量中的JSON格式错误: {e}")
                    return False
            else:
                # 尝试从文件读取凭据（本地开发用）
                credentials_file = 'credentials.json'
                if os.path.exists(credentials_file):
                    credentials = Credentials.from_service_account_file(
                        credentials_file, scopes=scope
                    )
                    logging.info("使用本地凭据文件")
                else:
                    logging.warning("未找到Google Sheets凭据（环境变量或文件）")
                    return False
            
            # 创建客户端
            self.client = gspread.authorize(credentials)
            
            # 打开电子表格和工作表
            if self.spreadsheet_id:
                spreadsheet = self.client.open_by_key(self.spreadsheet_id)
                self.worksheet = spreadsheet.worksheet(self.worksheet_name)
                logging.info(f"成功连接到Google Sheets: {self.spreadsheet_id}, 工作表: {self.worksheet_name}")
                return True
            else:
                logging.warning("未设置Google Sheets ID")
                return False
                
        except Exception as e:
            logging.error(f"连接Google Sheets失败: {e}")
            return False
    
    def log_visit(self, ip_address, user_agent, additional_info=None):
        """记录访问信息到Google Sheets"""
        try:
            if not self.worksheet:
                if not self.connect():
                    return False
            
            # 准备数据
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            data = [
                timestamp,
                ip_address,
                user_agent,
                additional_info or ''
            ]
            
            # 添加到工作表
            self.worksheet.append_row(data)
            
            logging.info(f"成功记录访问信息到Google Sheets: {ip_address}")
            return True
            
        except Exception as e:
            logging.error(f"记录访问信息失败: {e}")
            return False
    
    def get_visit_stats(self):
        """获取访问统计"""
        try:
            if not self.worksheet:
                if not self.connect():
                    return {'total': 0, 'today': 0}
            
            # 获取所有数据
            all_values = self.worksheet.get_all_values()
            
            if len(all_values) <= 1:  # 只有标题行
                return {'total': 0, 'today': 0}
            
            total_visits = len(all_values) - 1  # 减去标题行
            
            # 计算今日访问
            today = datetime.now().strftime('%Y-%m-%d')
            today_visits = sum(1 for row in all_values[1:] if row[0].startswith(today))
            
            return {
                'total': total_visits,
                'today': today_visits
            }
            
        except Exception as e:
            logging.error(f"获取访问统计失败: {e}")
            return {'total': 0, 'today': 0}
