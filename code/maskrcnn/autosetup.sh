echo y|conda create --name maskrcnn
conda activate maskrcnn
echo y|conda install ipython 
pip install ninja yacs cython matplotlib tqdm opencv-python
echo y|conda install pytorch torchvision cudatoolkit=10.0
export INSTALL_DIR=$PWD
cd $INSTALL_DIR
git clone https://github.com/cocodataset/cocoapi.git
cd cocoapi/PythonAPI
python setup.py build_ext install
cd $INSTALL_DIR
git clone https://github.com/NVIDIA/apex.git
cd apex
python setup.py install --cuda_ext --cpp_ext
cd $INSTALL_DIR
git clone https://github.com/facebookresearch/maskrcnn-benchmark.git
cd maskrcnn-benchmark
python setup.py build develop
unset INSTALL_DIR