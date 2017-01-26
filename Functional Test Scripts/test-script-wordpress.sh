#!/bin/bash
# To check is MySQL status
CHECK_MYSQL_STATUS="sudo /etc/init.d/mysql status"
HOSTNAME=$1
USERNAME=root
if [ $# -gt 1 ] ; then USERNAME=$2 ; fi

printf "\n\n##########################"
printf "\nTesting Tomcat,  MySQL, PHP and Wordpress"
printf "\nInstallation (WordPress Server)"
printf "\n##########################"

printf "\n\n*******************************************************"
printf "\nChecking the status of MySQL "
printf "\n*******************************************************\n"
ssh $SSHOPTS -l ${USERNAME} ${HOSTNAME} "${CHECK_MYSQL_STATUS}" | grep "Uptime" || { echo "TEST FAILED, mysql is not running" ; exit 31 ; }

printf "\n\n*******************************************************\n"
printf "Checking if the WordPress is RUNNING..."
printf "\nResponse received from the Server "

while read -r line
do
    echo "$line"
    if [[ $line == "200" ]]
    then
        echo "TEST 1 PASSED";
    else
        echo "TEST 1 FAILED";
        exit 32
    fi
done <<< $(curl -L -s -o /dev/null -w "%{http_code}" http://$1:80)

INDEX=$(curl -L -s -o - http://$1:80)
if [[ $INDEX == *"It works!"* ]]; then
    echo "TEST 2 PASSED"
else
    echo "TEST 2 FAILED"
    exit 32
fi