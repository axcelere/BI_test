import os
import time
import stat
import psycopg2
import datetime
import logging
import tempfile
from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError, _logger

_logger = logging.getLogger(__name__)

class ResConfigSettingsInherited(models.TransientModel):
    _inherit = 'res.config.settings'

    db_host = fields.Char(string = 'Database Host Name' , required=True)  # 'rds_host_url'
    db_user_name = fields.Char(string = 'Username', required=True)  # 'your_name'
    db_password = fields.Char(string = 'Password', required=True)  # 'your_db_password'
    db_name = fields.Char(string = 'Database Name', required=True)  # 'your_database_name'
    db_port = fields.Char(string = 'Database Port', required=True) # 'database_to_backup_name'
    file = fields.Binary(string='Upload',required=True) #'pgDump file'
    file_name = fields.Char(string="File Name")

    @api.model
    def run_script(self, *args, **kwargs):
        ICPSudo = self.env['ir.config_parameter'].sudo()
        db_host = ICPSudo.get_param("powerbi_script.db_host")
        user_name = ICPSudo.get_param("powerbi_script.db_user_name")
        db_name = ICPSudo.get_param("powerbi_script.db_name")
        port = ICPSudo.get_param("powerbi_script.db_port")
        pg_pass = ICPSudo.get_param("powerbi_script.db_password")
        db_bak_path = ICPSudo.get_param("powerbi_script.file_name")
        db_to_bak = self.env.cr.dbname

        import base64
        fd = base64.b64decode(ICPSudo.get_param("powerbi_script.file"))

        output = db_bak_path
        f = open(output,"wb")
        f.write(fd)
        f.close()
        
        from zipfile import ZipFile

        with ZipFile(output, 'r') as zipObj:
            listOfFileNames = zipObj.namelist()
            for fileName in listOfFileNames:
                if fileName.endswith('.sql'):
                    db_bak_path =  fileName
                    zipObj.extract(fileName)
                    break

        try:
            _logger.info('Restoring The Database to the RDS server')
            os.system('PGPASSWORD=%s dropdb --host %s --port "%s" --username %s --if-exists %s'%(pg_pass, db_host, port, user_name, db_to_bak))
            os.system('PGPASSWORD=%s createdb --host %s --port "%s" --username %s %s'%(pg_pass, db_host, port, user_name, db_to_bak))
            os.system('PGPASSWORD=%s psql --host %s --port "%s" --username %s -d %s -f %s' % (pg_pass, db_host, port, user_name, db_to_bak, db_bak_path))
            _logger.info('Restore Completed')
        except:
            print("Connection Error: Not connecting")


    def set_values(self):
        res = super(ResConfigSettingsInherited, self).set_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        connection = None
        try:
            connection = psycopg2.connect(
                database=self.db_name,
                user=self.db_user_name,
                password=self.db_password,
                host=self.db_host,
                port=self.db_port
            )
            ICPSudo.set_param("powerbi_script.db_host", self.db_host)
            ICPSudo.set_param("powerbi_script.db_user_name", self.db_user_name)
            ICPSudo.set_param("powerbi_script.db_password", self.db_password)
            ICPSudo.set_param("powerbi_script.db_name", self.db_name)
            ICPSudo.set_param("powerbi_script.db_port", self.db_port)
            ICPSudo.set_param("powerbi_script.file", self.file)
            ICPSudo.set_param("powerbi_script.file_name", self.file_name)
        except Exception as e:
            print(e)
            raise ValidationError("Incorrect credentials Please check and try again")
        finally:
            if connection:
                connection.close()
        return res
        
    @api.model
    def get_values(self):
        res = super(ResConfigSettingsInherited, self).get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()
        fields_dict = {
            
                            'db_host': ICPSudo.get_param("powerbi_script.db_host"),
                            'db_user_name': ICPSudo.get_param("powerbi_script.db_user_name"),
                            'db_password': ICPSudo.get_param("powerbi_script.db_password"),
                            'db_name': ICPSudo.get_param("powerbi_script.db_name"),
                            'db_port' : ICPSudo.get_param("powerbi_script.db_port"),
                            'file': ICPSudo.get_param('powerbi_script.file'),
                            'file_name': ICPSudo.get_param('powerbi_script.file_name')
                        }
        res.update(fields_dict)
        return res