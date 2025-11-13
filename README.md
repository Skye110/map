# map
🔧 Install Everything Inside a Virtual Environment (venv)
Follow these steps in your terminal, no overthinking.

1️⃣ Create venv
python -m venv venv


2️⃣ Activate it
Windows:
venv\Scripts\activate

Mac/Linux:
source venv/bin/activate

You’ll know it worked when your terminal suddenly starts looking like:
(venv) PS C:\Project>


3️⃣ Upgrade pip (trust me, GeoPandas is picky af)
pip install --upgrade pip


4️⃣ Install the core libraries
These cover Flask + your algorithms + graph building:
pip install flask
pip install shapely
pip install pyproj
pip install geopandas
pip install fiona
pip install rtree


5️⃣ If GeoPandas cries about dependencies
(Windows sometimes does this emotional damage):
Run:
pip install wheel
pip install --upgrade setuptools

Then:
pip install geopandas --no-cache-dir


6️⃣ Optional but probs needed for your project
pip install networkx  # even if you're not using it, some libs require it
pip install matplotlib
pip install numpy
pip install pandas


7️⃣ Check everything installed
pip list

If you see geopandas, shapely, pyproj, flask — you’re golden.

💫 Done
You’re now running a clean, isolated environment where your graph algorithms, shapefiles, and Flask setup won’t explode randomly.
If you want, I can also make you a requirements.txt for this entire project.
https://download.geofabrik.de/asia/mongolia.html 
download the MONGOLIA map data set
