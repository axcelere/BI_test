# -*- coding: utf-8 -*-
import datetime as datetime
import psycopg2
import base64
import pdb
import threading, odoo
import datetime
from zipfile import ZipFile
from odoo import models, fields, api, os
from odoo.exceptions import ValidationError, UserError, _logger


class odoosh_bi(models.Model):
    _name = 'odoosh_bi.odoosh_bi'
    _description = 'odoosh_bi.odoosh_bi'

    db_host = fields.Char(string='Database Host Name', required=True)  # 'rds_host_url'
    db_user_name = fields.Char(string='Username', required=True)  # 'your_name'
    db_password = fields.Char(string='Password', required=True)  # 'your_db_password'
    db_name = fields.Char(string='Database Name', required=True)  # 'your_database_name'
    db_port = fields.Char(string='Database Port', required=True)  # 'database_to_backup_name'
    db_file = fields.Binary(string='Upload', required=True)  # 'pgDump file'
    db_create_for_backup = fields.Char(string='Create DB For Backup', required=True)
    last_updated_RDS = fields.Text(string=' last RDS update', default='Not Used Yet !!!!', readonly=True)
    Logs = fields.Text(string='logs', default='No Logs yet !!!!', readonly=True)

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
                    print("database is empty")
                    connection.close()
                    return True
                else:
                    print("database is not empty")
                    connection.close()
                    return False
        except Exception as e:
            print(e)
        finally:
            if connection:
                connection.close()


    def _run_process(self, id):
        with api.Environment.manage():
            with odoo.registry(self.env.cr.dbname).cursor() as new_cr:
                new_env = api.Environment(new_cr, self.env.uid, self.env.context)
                obj = new_env['odoosh_bi.odoosh_bi'].sudo().search([('id', '=', id)])
                db_host = obj.db_host
                user_name = obj.db_user_name
                db_name = obj.db_create_for_backup
                port = obj.db_port
                pg_pass = obj.db_password
                db_to_bak = obj.db_name
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

                try:
                    _logger.info('Restoring The Database to the RDS server')
                    now = str(datetime.datetime.now())
                    old_log = obj.Logs
                    obj.Logs = now + ' Restoring The Database to the RDS server \n' + old_log

                    os.system('PGPASSWORD=%s dropdb --host %s --port "%s" --username %s --if-exists %s' % (
                        pg_pass, db_host, port, user_name, db_to_bak))

                    os.system('PGPASSWORD=%s createdb --host %s --port "%s" --username %s %s' % (
                        pg_pass, db_host, port, user_name, db_to_bak))
                    
                    
                    status = self.checkupdate(val)
                    if status == True:
                        now = str(datetime.datetime.now())
                        obj.last_updated_RDS = now

                        os.system('PGPASSWORD=%s psql --host %s --port "%s" --username %s -d %s -f %s' % (
                            pg_pass, db_host, port, user_name, db_to_bak, db_bak_path))

                        # check database empty or not if not empty upload success
                        status = self.checkupdate(val)
                        # status = False
                        if status == False:
                            _logger.info('Restore Completed')
                            now = str(datetime.datetime.now())
                            old_log = obj.Logs
                            obj.Logs = now + ' Restore Completed \n' + old_log

                            now = str(datetime.datetime.now())
                            obj.last_updated_RDS = now + ' Restore Completed \n'
                        else:
                            # print("Some Error While Restoring Database")
                            obj.last_updated_RDS = 'Error While Restoring Database'
                            _logger.info("Error While Restoring Database")

                            now = str(datetime.datetime.now())
                            old_log = obj.Logs
                            obj.Logs = now + ' Error While Restoring Database \n' + old_log
                            return

                    else:
                        print("Database is Being Used Somewhere")
                        obj.last_updated_RDS = "Database is Being Used Somewhere"
                        _logger.info("Database is Being Used Somewhere")
                        now = str(datetime.datetime.now())
                        old_log = obj.Logs
                        obj.Logs = now + ' Database is Being Used Somewhere \n' + old_log

                except  Exception as e:
                    print(e)
                    obj.last_updated_RDS = "Error While Restoring Database"
                    # print("Connection Error: Not connecting")
                    now = str(datetime.datetime.now())
                    old_log = obj.Logs
                    obj.Logs = now + ' ' + e +' \n' + old_log

    @api.model
    def run_script(self, *args, **kwargs):
        obj = threading.Thread(target=self._run_process, args=(args[0][0],))
        obj.start()


    @api.model
    def create(self, vals):
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
        print(vals, self)
        obj = self.env['odoosh_bi.odoosh_bi'].sudo().search([('id', '=', self.id)])
        print(obj)
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
