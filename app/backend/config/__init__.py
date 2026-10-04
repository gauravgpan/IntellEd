import pymysql

# PyMySQL needs no system libmysqlclient build — it's a pure-Python driver,
# registered here so Django's mysql backend (which expects MySQLdb) can use it.
pymysql.install_as_MySQLdb()
pymysql.version_info = (1, 4, 6, "final", 0)
