# StitchPro
Python app for reconstruction of tissue quadrants into a complete pseudo-whole-mount histopathology prostate section.

This repository includes the Python algorithm developed for stitching of prostate quadrants into an entire prostate section. Our algorithm is based in three main steps - boundary detection, histogram matching, and differential evolution optimization - and is intuitive to run as a Streamlit application, keeping the user input to a minimum who only needs to provide as arguments the tissue fragments to be reconstructed.
 
### Repository Structure
- StitchPro.py: Python algorithm for stitching.
- requirements.txt: Text file with the necessary Python packages for this algorithm.

### Compatibility
The four quadrants need to be image files provided in TIFF (.tif) format.

### Usage
This algorithm was created to be run as a streamlit application.

1) Clone this repository to your local folder;

2) Install the necessary Python packages under requirements.txt;

3) Go to your local folder and run the app using the command line:
`$ streamlit run StitchPro.py`

4) On the app upload the four quadrant images to be reconstructed and, for each quadrant, modify the angle to rotate the fragments, the median filter size and the binary closing footprint parameters (if necessary), and press "Start stitching!".

### Acknowledgements
This study was approved by the Champalimaud Foundation Ethics Commitee, under the ProCAncer-I project. This work was funded by the European Union’s Horizon 2020 research and innovation programme (grant 952159) and by Fundação para a Ciência e Tecnologia UIDB/00645/2020 and https://doi.org/10.54499/UIDB/00645/2020.
This repository was created by Ana Sofia Castro Verde. For questions, please contact ana.castroverde@research.fchampalimaud.org.

### Cite us
If you use this algorithm in your work, please cite us with:

A. S. C. Verde, J. G. Almeida, J. Fonseca, C. Matos, R. C. Conceição, N. Papanikolaou, "StitchPro for computational pathology stitching in patients with prostate cancer", 4-page paper accepted for the IEEE International Symposium on Biomedical Imaging (ISBI) 2024.

