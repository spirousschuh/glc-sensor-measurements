More docu
=========

Just a dummy file

Network Issues
--------------

You might encounter that your raspberry pi does not connect to the internet
even though there is a cable plugged in. In this case

.. code-block:: sh
    :caption: fix network issues

    sudo dhclient eth0

That command tells the switch to give you a new ip adress for the `eth0` interface.


something
_________