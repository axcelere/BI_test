# import gzip
# input = gzip.GzipFile("file.tar.gz","rb")
# s = input.read()
# input.close()
# output = open("file.txt",'wb')
# output.write(s)
# output.close()
# print("done")

# with gzip.open("file.tar.gz","rb") as f:
#     f.write(data)
# import tarfile
# filename = "file.tar.gz"
# tf = tarfile.open(filename)
# tf.extractall('/opt/odoo/odoo/custom_addons/techneith-powerbi_script-4a3c53b78bb1/models')
import os

os.popen('sh odoo.sh')
