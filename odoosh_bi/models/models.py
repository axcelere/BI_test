# -*- coding: utf-8 -*-
import datetime as datetime
import psycopg2
import base64
import pdb
import threading, odoo
import datetime
from zipfile import ZipFile
from odoo import models, fields, api, os
from odoo.exceptions import ValidationError, UserError, _logger, Warning


class odoosh_bi(models.Model):
    _name = 'odoosh_bi.odoosh_bi'
    _description = 'odoosh_bi.odoosh_bi'

    db_host = fields.Char(string='Database Host Name')  # 'rds_host_url'
    db_user_name = fields.Char(string='Username')  # 'your_name'
    db_password = fields.Char(string='Password')  # 'your_db_password'
    db_name = fields.Char(string='Database Name')  # 'your_database_name'
    db_port = fields.Char(string='Database Port')  # 'port'
    db_file = fields.Binary(string='Upload' )  # 'pgDump file'
    db_name_for_backup = fields.Char(string='Create DB For Backup')
    last_updated_RDS = fields.Text(string='last RDS update', default="Logs:__")
    logs = fields.Text(string='logs', default="Logs:_")
    blockFlag = fields.Boolean(string='Block Flag', default=False)

    @api.model
    def checkupdate(self, vals):
        connection = None
        try:
            connection = psycopg2.connect(
                database=vals['database'],
                user=vals['user'],
                password=vals['password'],
                host=vals['host'],
                port=vals['port']
            )
            
            if connection:
                cursor = connection.cursor()
                check_table = '''select count(*) from information_schema.tables where table_schema = 'public';'''
                cursor.execute(check_table)
                list_tables = cursor.fetchall()
                # print(list_tables)
                if (list_tables == [(0,)]):
                    # print("database is empty")
                    connection.close()
                    return True
                else:
                    # print("database is not empty")
                    connection.close()
                    return False
        except Exception as e:
            print(e)
        finally:
            if connection:
                connection.close()

    def _run_process(self, id):
        # print(self.env['ir.config_parameter'])
        # self.env['ir.config_parameter'].set_param(id, False)
        # print(self.env['ir.config_parameter'])
        # print(self.localcontext)
        # print(self.localcontext.update({id: False}))
        # print(self.localcontext)
        with api.Environment.manage():
            with odoo.registry(self.env.cr.dbname).cursor() as new_cr:
                new_env = api.Environment(new_cr, self.env.uid, self.env.context)
                obj = new_env['odoosh_bi.odoosh_bi'].sudo().search([('id', '=', id)])
                db_host = obj.db_host
                user_name = obj.db_user_name
                db_name = obj.db_name_for_backup
                port = obj.db_port
                pg_pass = obj.db_password
                db_to_bak = db_name
                output = "backup_file.zip"
                db_bak_path = ''
                
                val = {
                    'database': db_name,
                    'user': user_name,
                    'password': pg_pass,
                    'host': db_host,
                    'port': port
                }

                try:
                    if os.path.exists(output):
                        os.remove(output)

                    fd = base64.b64decode(obj.db_file)
                    f = open(output, "wb")
                    f.write(fd)
                    f.close()
                except Exception as e:
                    print(e)
                    return

                try:
                    with ZipFile(output, 'r') as zipObj:
                        listOfFileNames = zipObj.namelist()
                        for fileName in listOfFileNames:
                            if fileName.endswith('.sql'):
                                db_bak_path = fileName
                                zipObj.extract(fileName)
                                break
                except:
                    print("Zip extraction error")
                    return
                
                # size = len(obj.logs)
                # if size > 1000:
                #     size = 1000
                # curr_logs = str(obj.logs[0:size]) or ''
                try:
                    _logger.critical('Restoring The Database to the RDS server')

                    os.system('PGPASSWORD=%s dropdb --host %s --port "%s" --username %s --if-exists %s' % (
                        pg_pass, db_host, port, user_name, db_to_bak))

                    os.system('PGPASSWORD=%s createdb --host %s --port "%s" --username %s %s' % (
                        pg_pass, db_host, port, user_name, db_to_bak))
                    
                    status = self.checkupdate(val)
                    if status == True:
                        os.system('PGPASSWORD=%s psql --host %s --port "%s" --username %s -d %s -f %s' % (
                            pg_pass, db_host, port, user_name, db_to_bak, db_bak_path))

                        status = self.checkupdate(val)
                        if status == False:
                            _logger.critical('Restore Completed')
                            # obj.write({'blockFlag': False})
                            # obj.blockFlag = False
                            # now = str(datetime.datetime.now())
                            # obj.write({'last_updated_RDS': now + ' Restore Completed',
                            # 'logs':  now + ' Restore Completed \n' + curr_logs,
                            # 'blockFlag': False})
                        else:
                            _logger.critical("Error While Restoring Database")
                            # now = str(datetime.datetime.now())
                            # obj.write({'last_updated_RDS': now + ' Error While Restoring Database',
                            # 'logs':  now + ' Error While Restoring Database \n' + curr_logs,
                            # 'blockFlag': False})
                            # obj.write({'blockFlag': False})
                    else:
                        _logger.critical("Database is Being Used Somewhere")
                        # now = str(datetime.datetime.now())
                        # curr_logs = now + ' Database is Being Used Somewhere \n' + curr_logs
                        # obj.write({'last_updated_RDS': now + " Database is Being Used Somewhere",
                        #     'logs':  curr_logs})
                        # obj.write({'blockFlag': False})
                        # obj.blockFlag = False
                    
                except Exception as e:
                    _logger.critical("Error While Restoring Database", e)
                    # now = str(datetime.datetime.now())
                    # obj.write({'last_updated_RDS': now + ' Error While Restoring Database',
                    #     'logs':  now + ' Error While Restoring Database \n' + curr_logs,
                    #     'blockFlag': False})
                    # obj.write({'blockFlag': False})
                    # obj.blockFlag = False


    def run_script(self, *args, **kwargs):
        # print(self.env['ir.config_parameter'])
        # print(self.localcontext)
        id = self.id # args[0][0]
        # self.env['ir.config_parameter'].set_param(id, True)
        # print(self.localcontext.update({id: True}))
        obj = self.env['odoosh_bi.odoosh_bi'].sudo().search([('id', '=', id)])
        # size = len(obj.logs)
        # if size > 1000:
        #     size = 1000
        # curr_logs = str(obj.logs[0:size]) or ''
        try:
            if not obj.blockFlag:
                now = str(datetime.datetime.now())
                # obj.last_updated_RDS =  now + " Restoring The Database to the RDS server"
                # obj.logs = now + ' Restoring The Database to the RDS server \n' + curr_logs
                # obj.blockFlag = True
                # obj.write({'blockFlag': True})
                # curr_logs = now + ' Restoring The Database to the RDS server \n' + curr_logs
                # self.write({'last_updated_RDS': now + " Restoring The Database to the RDS server",
                #            'logs':  curr_logs,
                #            'blockFlag': True})
                obj = threading.Thread(target=self._run_process, args=(id,))
                obj.start()
                obj.join()
                # now = str(datetime.datetime.now())
                # self.write({'last_updated_RDS': now + ' Restore Completed',
                #         'logs':  now + ' Restore Completed \n' + curr_logs,
                #         'blockFlag': False})

            else:
                raise ValidationError("Backup script is already in progress")
        except Exception as e:
            print(e)
            _logger.critical("Error While Restoring Database", e)
        
    @api.model
    def create(self, vals):
        if 'db_name_for_backup' in vals:
            vals['db_name_for_backup'] = vals['db_name_for_backup'].replace(" ", "")
            obj = self.env['odoosh_bi.odoosh_bi'].sudo().search([('db_name_for_backup', '=', vals['db_name_for_backup'])]).ids
            if obj:
                raise ValidationError("Database name is not unique, already been used in other backup")
        
        connection = None
        try:
            connection = psycopg2.connect(
                database=vals['db_name'],
                user=vals['db_user_name'],
                password=vals['db_password'],
                host=vals['db_host'],
                port=vals['db_port']
            )

        except Exception as e:
            print(e)
            raise ValidationError("Incorrect credentials Please check and try again")
        finally:
            if connection:
                connection.close()
        return super(odoosh_bi, self).create(vals)


    def write(self, vals):
        if 'db_name_for_backup' in vals:
            vals['db_name_for_backup'] = vals['db_name_for_backup'].replace(" ", "")
            obj = self.env['odoosh_bi.odoosh_bi'].sudo().search([('db_name_for_backup', '=', vals['db_name_for_backup'])]).ids
            if len(obj) > 0 or (len(obj) == 1 and self.id not in obj):
                raise ValidationError("Database name is not unique, already been used in other backup")
        print(vals, self)
        obj = self.env['odoosh_bi.odoosh_bi'].sudo().search([('id', '=', self.id)])
        # print(obj)
        updated_vals = {
            'db_name': obj.db_name,
            'db_user_name': obj.db_user_name,
            'db_password': obj.db_password,
            'db_host': obj.db_host,
            'db_port': obj.db_port
        }
        for i in vals:
            updated_vals[i] = vals[i]
        connection = None
        try:
            connection = psycopg2.connect(
                database=updated_vals['db_name'],
                user=updated_vals['db_user_name'],
                password=updated_vals['db_password'],
                host=updated_vals['db_host'],
                port=updated_vals['db_port']
            )
        except Exception as e:
            print(e)
            raise ValidationError("Incorrect credentials Please check and try again")
        finally:
            if connection:
                connection.close()
        return super(odoosh_bi, self).write(vals)
