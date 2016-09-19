# Image-Server-Initialisation
Python script to programatically retrieve an image and use this image to create and launch a new server instance on the FCO platform.

Authentication variables for the FCO API such as customer username, customer UUID and customer password which are used by all scripts in the application are contained in the globals.py file and need to set to valid parameters.

**globalUsername** (The username/email address of the customer account to be used for authentication)

**globalCustomerUUID** (The customer UUID)

**globalPassword** (The customers password)

**globalENDPOINT** (Default for the FCO platform is https://cp.sd1.flexiant.net:4442/)

Inside the rest_post_image method in the getImage.py file, various parameters will need to be set.  These include:

**resourceURL** (the URL of the image which is to be imported into the system)

**vdcUUID** (the UUID of the VDC which the image will belong to)

**productoUUID** (the product offer UUID of the disk which will house the new image)

**imageName** (the name which will be assigned to the new image)

**clusteruuid** (the UUID of the cluster which the image will belong to)

**default_user** (the default username which will be set on the image (optional))

**gen_password** (boolean value specifying if a password should be generated for the image)

**size** (the size of the disk which will contain the image)

The method create_server() in serverCreation.py contains the parameters which must be set in order for the script to create a new server instance.

These variables are:

**servername** (the name which is to be assigned to the new server)

**server_productoffer_uuid** (the product offer UUID which is to be assigned to the new server)

**cluster_uuid** (the UUID of the cluster in which the server will belong to)

**vdc_uuid** (the UUID of the VDC in which the new server will belong to)

**cpu_count** (the number of CPUs the new server will have)

**ram_amount** (the amount of RAM the new server will have)

**boot_disk_po_uuid** (the UUID of the product offer of the boot disk which is to be used for the new server)

**context_script** (a context script to be run on the new server upon creation (optional))

**networkUUID** (the UUID of the network in which the NIC is to belong to)

**networkType** (the type of the network which the NIC is to operate on (e.g. IP))

**resourceName** (the name of the NIC resource)

**resourceType** (the type of the NIC resource)
