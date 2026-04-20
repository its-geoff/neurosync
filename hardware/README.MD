For hardware to work a 25 MHz clk must be generated in vivado using IP catalog
Step 1: Add the Clocking Wizard IP
Open Vivado and go to the IP Catalog.
Search for Clocking Wizard.
Double-click it to add it to the project.
Name the component (e.g., clk_wiz_0).
Step 2: Configure the Clocking Wizard
In the configuration window:
Set the Input Clock Frequency to 100 MHz.
Go to the Output Clocks tab.
Enable clk_out1.

Set the output frequency to:

25 MHz
Leave other settings as default.
Click OK.
Step 3: Generate the IP

After adding the Clocking Wizard, click:

Generate Output Products
Wait for Vivado to finish generating the IP files.
Step 4: Disable the Clocking Wizard XDC File

The Clocking Wizard automatically generates a constraint file that incorrectly creates a duplicate clock on the input.

To fix this:

In the Sources panel, go to:

Constraints

Locate the Clocking Wizard constraint file, typically named:

clk_wiz_0.xdc
Right-click on the file.

Select:
Disable File