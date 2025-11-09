#!/bin/bash

# Define the absolute path to your virtual environment's python interpreter
PYTHON="/path/to/venv/bin/python" 

# Define the absolute path to your manage.py script
MANAGE_PY="/opt/django_project/manage.py" 

# The Python command executes the deletion and prints the timestamp and count
PYTHON_ONE_LINER="from datetime import timedelta, datetime; from crm.models import Customer; cutoff_date = datetime.now() - timedelta(days=365); count, _ = Customer.objects.filter(last_order_date__lt=cutoff_date).delete(); print(\"$(date '+%Y-%m-%d %H:%M:%S') - Deleted: {}\".format(count))"

# Execute the command and redirect all output to the log file
$PYTHON $MANAGE_PY shell --command="$PYTHON_ONE_LINER" >> /tmp/customer_cleanup_log.txt 2>&1

# Ensure the script exits successfully
exit 0
