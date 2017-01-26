#!/bin/bash
printf "\n\n##########################"
printf "\nTesting Tomcat, MySQL and PHP"
printf "\nInstallations"
printf "\n##########################"

USERNAME=root
if [ $# -gt 1 ] ; then USERNAME=$2 ; fi
HOSTNAME=$1

# To check if apache is RUNNING
# To check if MySQL is INSTALLED
CHECK_MYSQL="mysql \-\-version"
# To check is MySQL status
CHECK_MYSQL_STATUS="sudo /etc/init.d/mysql status"

printf "\n\n*******************************************************"
printf "\nChecking if MySQL has been installed "
printf "\n*******************************************************\n"
ssh -l ${USERNAME} ${HOSTNAME} "${CHECK_MYSQL}"

printf "\n\n*******************************************************"
printf "\nChecking the status of MySQL "
printf "\n*******************************************************\n"
ssh -l ${USERNAME} ${HOSTNAME} "${CHECK_MYSQL_STATUS}"

# Add a test.php file to test the apache installation and php
ssh -l ${USERNAME} ${HOSTNAME} "echo \"<?php phpinfo(); ?>\" > /tmp/test.php"
ssh -l ${USERNAME} ${HOSTNAME} "sudo mv /tmp/test.php /var/www/."

printf "\n*******************************************************\n"
printf "Checking if the LAMP stack is RUNNING..."
printf "Response received from the Server "
while read -r line
do
    echo "$line"
    if [[ $line == "200" ]]
    then
        echo "TEST PASSED, LAMP stack IS RUNNING";
    else
        echo "TEST FAILED";
    fi

done <<< $(curl -s -o /dev/null -w "%{http_code}" http://$1/test.php)
