# DeepMove
application of fish classification using hybrid HOGY alogorithm

 # GMM Output
Run "opencv_gmm.py" to save gmm frames
# Optical Output
Run "opencv_opencv.py" to save optical frames from the given video
# YOLO Output
Tun " opencv_yolo.py" to save YOLO detections on the provided video
# Combining Optical and GMM instances
Run " comb_gmm_optical_images.py" to combing gmm and optical flow instances and do fish detection and classification on all frames
# Preferential Combination
Run "preferential_combination .py" to combine YOLO detections with GMM-Optical combined classified output in a preferential manner where YOLO results will be given preference over the overlapping results and final output will be saved
# Visualize the results
Run " show_images.py" by specifying the input folder to see all annotated data from the respective algorithm
# Application
Run "deepmove.py" to see the GUI of the application
