import os
import warnings

def setup_environment():
    os.environ['TRANSFORMERS_NO_TF'] = '1'
    os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
    os.environ['TRANSFORMERS_VERBOSITY'] = 'error'
    os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
    
    warnings.filterwarnings('ignore')
