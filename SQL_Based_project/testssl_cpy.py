#!/usr/bin/env python

import os
import sys
import ssl
import socket
import platform

import mysql.connector

print("os:            " + platform.platform())
print("python         " + sys.version)
print("openssl:       " + ssl.OPENSSL_VERSION)
print("TLSv1.2:       " + str(ssl.PROTOCOL_TLSv1_2))

parameters = {
    'ssl_verify_cert': True,
    'ssl_ca': '/home/pjesus/mysql-sandboxes/3300/sandboxdata/ca.pem',
    'host': 'localhost',
    'user': 'root',
    'port': 3300,
    'passwd': 'password123'
}

db_conn = mysql.connector.connect(**parameters)

cur = db_conn.cursor()
cur.execute("SHOW STATUS LIKE 'Ssl_version'")
results = cur.fetchall()
print(results)

cur.execute("SHOW STATUS LIKE 'Ssl_cipher'")
results = cur.fetchall()
print(results)

cur.execute("SHOW VARIABLES LIKE 'tls_version'")
results = cur.fetchall()
print(results)

cur.close()

db_conn.close()

print("done")