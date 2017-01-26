#!/bin/bash
printf "\n\n##########################"
printf "\nTesting Tomcat and MySQL" 
printf "\nInstallation (MySQL Server)"
printf "\n##########################"

USERNAME=root
HOSTNAME=$1
if [ $# -gt 1 ] ; then USERNAME=$2 ; fi

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

printf "\n*******************************************************\n"
printf "Checking if the MySQL Server is RUNNING..."
printf "Response received from the Server "
while read -r line
do
    echo "$line"
    if [[ $line == *"200"* ]]
    then
  	echo "TEST PASSED, MySQL SERVER IS RUNNING";
    else
	echo "TEST FAILED";
    fi
	
done <<< $(curl -s -o /dev/null -w "%{http_code}" http://$1)
