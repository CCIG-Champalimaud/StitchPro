"""
# StitchPro
"""
## Import packages

import streamlit as st
import imageio.v2 as imageio
import matplotlib.pyplot as plt
import cv2
from PIL import Image, ImageEnhance
import numpy as np
from skimage import color, data
import scipy.ndimage as ndi
from skimage import morphology
from skimage.feature import canny, corner_harris, corner_subpix, corner_peaks
from itertools import combinations
from scipy.spatial.distance import cdist, pdist, squareform
from skimage.transform import rescale, resize
import argparse
import tifffile
from tiatoolbox.wsicore import WSIReader
import time

## App description
st.title("StitchPro")

st.subheader("This app was created for reconstruction of tissue quadrants into \
        a complete pseudo-whole-mount histopathology prostate section.")
st.write("Please upload your images below:")
st.sidebar.write("Intermediate steps viewer:")
start_time = time.time()

## Upload images and rotate them by given angle
img_file_buffer_ur = st.file_uploader("Upper-right (UR) fragment:", type=["tiff"])
img_file_buffer_lr = st.file_uploader("Lower-right (LR) fragment:", type=["tiff"])
img_file_buffer_ll = st.file_uploader("Lower-left (LL) fragment:", type=["tiff"])
img_file_buffer_ul = st.file_uploader("Upper-left (UL) fragment:", type=["tiff"])

if (img_file_buffer_ur is not None) & (img_file_buffer_lr is not None) & (img_file_buffer_ll is not None) & (img_file_buffer_ul is not None):
    histo_fragment_ur = imageio.imread(img_file_buffer_ur)
    st.sidebar.image(histo_fragment_ur, caption="UR fragment", use_column_width=True)
    histo_fragment_lr = imageio.imread(img_file_buffer_lr)
    st.sidebar.image(histo_fragment_lr, caption="LR fragment", use_column_width=True)
    histo_fragment_ll = imageio.imread(img_file_buffer_ll)
    st.sidebar.image(histo_fragment_ll, caption="LL fragment", use_column_width=True)
    histo_fragment_ul = imageio.imread(img_file_buffer_ul)
    st.sidebar.image(histo_fragment_ul, caption="UL fragment", use_column_width=True)

    angle_options = [-90, 0, 90, 180]
    angle_choice_ur = st.selectbox("Angle to rotate the UR fragment", angle_options, index = 1)
    if int(angle_choice_ur) == 90:
        histo_fragment_ur = cv2.rotate(histo_fragment_ur, cv2.ROTATE_90_CLOCKWISE)
    if int(angle_choice_ur) == -90:
        histo_fragment_ur = cv2.rotate(histo_fragment_ur, cv2.ROTATE_90_COUNTERCLOCKWISE)
    if int(angle_choice_ur) == 180:
        histo_fragment_ur = cv2.rotate(histo_fragment_ur, cv2.ROTATE_180)
    if int(angle_choice_ur) == 0:
        histo_fragment_ur = histo_fragment_ur
    angle_choice_lr = st.selectbox("Angle to rotate the LR fragment", angle_options, index = 1)
    if int(angle_choice_lr) == 90:
        histo_fragment_lr = cv2.rotate(histo_fragment_lr, cv2.ROTATE_90_CLOCKWISE)
    if int(angle_choice_lr) == -90:
        histo_fragment_lr = cv2.rotate(histo_fragment_lr, cv2.ROTATE_90_COUNTERCLOCKWISE)
    if int(angle_choice_lr) == 180:
        histo_fragment_lr = cv2.rotate(histo_fragment_lr, cv2.ROTATE_180)
    if int(angle_choice_lr) == 0:
        histo_fragment_lr = histo_fragment_lr
    angle_choice_ll = st.selectbox("Angle to rotate the LL fragment", angle_options, index = 1)
    if int(angle_choice_ll) == 90:
        histo_fragment_ll = cv2.rotate(histo_fragment_ll, cv2.ROTATE_90_CLOCKWISE)
    if int(angle_choice_ll) == -90:
        histo_fragment_ll = cv2.rotate(histo_fragment_ll, cv2.ROTATE_90_COUNTERCLOCKWISE)
    if int(angle_choice_ll) == 180:
        histo_fragment_ll = cv2.rotate(histo_fragment_ll, cv2.ROTATE_180)
    if int(angle_choice_ll) == 0:
        histo_fragment_ll = histo_fragment_ll
    angle_choice_ul = st.selectbox("Angle to rotate the UL fragment", angle_options, index = 1)
    if int(angle_choice_ul) == 90:
        histo_fragment_ul = cv2.rotate(histo_fragment_ul, cv2.ROTATE_90_CLOCKWISE)
    if int(angle_choice_ul) == -90:
        histo_fragment_ul = cv2.rotate(histo_fragment_ul, cv2.ROTATE_90_COUNTERCLOCKWISE)
    if int(angle_choice_ul) == 180:
        histo_fragment_ul = cv2.rotate(histo_fragment_ul, cv2.ROTATE_180)
    if int(angle_choice_ul) == 0:
        histo_fragment_ul = histo_fragment_ul

    images_original = [histo_fragment_ur, histo_fragment_lr, histo_fragment_ll, histo_fragment_ul]

    original_spacing = st.slider("Original image spacing (micrometers):", 0.0, 1.0, 0.25)
    level = st.slider("Downsampling level:", 0, 10, 5)
    out_path = st.text_input("Insert file path (e.g. /Users/username/Documents/folder/):", "")
    sub_bound_x = st.slider("Value to subtract from x boundary of output image:", 0, 1000, 550)
    sub_bound_y = st.slider("Value to subtract from y boundary of output image:", 0, 1000, 550)

    # Downsample the images
    DOWNSAMPLE_LEVEL = 4  # avoid running the optimization for the entire image
    add = 0
    histo_fragment_lr = rescale(histo_fragment_lr, 1 / DOWNSAMPLE_LEVEL, channel_axis=2,
                                preserve_range=True).astype(np.uint8)
    histo_fragment_ll = rescale(histo_fragment_ll, 1 / DOWNSAMPLE_LEVEL, channel_axis=2,
                                preserve_range=True).astype(np.uint8)
    histo_fragment_ur = rescale(histo_fragment_ur, 1 / DOWNSAMPLE_LEVEL, channel_axis=2,
                                preserve_range=True).astype(np.uint8)
    histo_fragment_ul = rescale(histo_fragment_ul, 1 / DOWNSAMPLE_LEVEL, channel_axis=2,
                                preserve_range=True).astype(np.uint8)

    ### Find image contours

    ## Convert from RGB image to grayscale
    histo_fragment_gray_binary_ll = color.rgb2gray(histo_fragment_ll)
    histo_fragment_gray_ll = (histo_fragment_gray_binary_ll * 256).astype('uint8')
    histo_fragment_gray_binary_lr = color.rgb2gray(histo_fragment_lr)
    histo_fragment_gray_lr = (histo_fragment_gray_binary_lr * 256).astype('uint8')
    histo_fragment_gray_binary_ul = color.rgb2gray(histo_fragment_ul)
    histo_fragment_gray_ul = (histo_fragment_gray_binary_ul * 256).astype('uint8')
    histo_fragment_gray_binary_ur = color.rgb2gray(histo_fragment_ur)
    histo_fragment_gray_ur = (histo_fragment_gray_binary_ur * 256).astype('uint8')

    ## Intensity histogram
    hist_ul = ndi.histogram(histo_fragment_gray_ul, min=0, max=255, bins=256)
    hist_ur = ndi.histogram(histo_fragment_gray_ur, min=0, max=255, bins=256)
    hist_lr = ndi.histogram(histo_fragment_gray_lr, min=0, max=255, bins=256)
    hist_ll = ndi.histogram(histo_fragment_gray_ll, min=0, max=255, bins=256)

    ## Image segmentation based on threshold
    thresh = 220

    image_thresholded_ul = histo_fragment_gray_ul < thresh
    image_thresholded_ur = histo_fragment_gray_ur < thresh
    image_thresholded_lr = histo_fragment_gray_lr < thresh
    image_thresholded_ll = histo_fragment_gray_ll < thresh

    ## Apply median filter to reduce the noise
    median_filter_ur_x = st.slider('Median filter size for UR', 5, 50, 20)
    median_filter_lr_x = st.slider('Median filter size for LR', 5, 50, 20)
    median_filter_ll_x = st.slider('Median filter size for LL', 5, 50, 20)
    median_filter_ul_x = st.slider('Median filter size for UL', 5, 50, 20)
    image_thresholded_filtered_ul = ndi.median_filter(image_thresholded_ul, size=int(median_filter_ul_x))
    image_thresholded_filtered_ur = ndi.median_filter(image_thresholded_ur, size=int(median_filter_ur_x))
    image_thresholded_filtered_ll = ndi.median_filter(image_thresholded_ll, size=int(median_filter_ll_x))
    image_thresholded_filtered_lr = ndi.median_filter(image_thresholded_lr, size=int(median_filter_lr_x))

    ## Erode the image to eliminate holes
    closing_ur_x = st.slider('Binary closing footprint for UR', 5, 50, 15)
    closing_lr_x = st.slider('Binary closing footprint for LR', 5, 50, 15)
    closing_ll_x = st.slider('Binary closing footprint for LL', 5, 50, 15)
    closing_ul_x = st.slider('Binary closing footprint for UL', 5, 50, 15)
    image_thresholded_filtered_closed_ul = morphology.binary_closing(image_thresholded_filtered_ul,
                                                                     footprint=morphology.square(
                                                                         int(closing_ul_x)))  # morphology.square(30) 28 disk
    image_thresholded_filtered_closed_ur = morphology.binary_closing(image_thresholded_filtered_ur,
                                                                     footprint=morphology.square(
                                                                         int(closing_ur_x)))  # morphology.square(84) 26
    image_thresholded_filtered_closed_ll = morphology.binary_closing(image_thresholded_filtered_ll,
                                                                     footprint=morphology.square(
                                                                         int(closing_ll_x)))  # morphology.square(100) 30
    image_thresholded_filtered_closed_lr = morphology.binary_closing(image_thresholded_filtered_lr,
                                                                     footprint=morphology.square(
                                                                         int(closing_lr_x)))  # morphology.square(150) 26

    # Identify the image boundary
    canny_edges_ul = canny(image_thresholded_filtered_closed_ul, sigma=5)
    canny_edges_ur = canny(image_thresholded_filtered_closed_ur, sigma=5)
    canny_edges_ll = canny(image_thresholded_filtered_closed_ll, sigma=5)
    canny_edges_lr = canny(image_thresholded_filtered_closed_lr, sigma=5)

    if st.button("Start stitching!")==True:
        def circle_arc_loss_cv(par, mask, pad=20):
            mask = cv2.copyMakeBorder(
                mask, pad, pad, pad, pad, cv2.BORDER_CONSTANT)
            cx, cy, r1, r2, theta_1, theta_plus = par
            cx, cy = cx + pad, cy + pad
            theta_2 = theta_1 + theta_plus
            theta_1, theta_2 = np.rad2deg([theta_1, theta_2])
            O = np.zeros_like(mask)
            cv2.ellipse(O, (int(cy), int(cx)), (int(r1), int(r2)), angle=0,
                        startAngle=theta_1, endAngle=theta_2, color=1,
                        thickness=-1)
            fn = np.sum((mask == 1) & (O == 0))
            I = np.sum(O * mask)
            U = np.sum(O + mask) - I
            return 1 - I / U + fn / mask.sum()


        def calculate_intersection(m1, b1, m2, b2):
            cx = (b2 - b1) / (m1 - m2)
            cy = m1 * cx + b1
            return cx, cy


        def pol2cart(rho, phi):
            # from https://stackoverflow.com/questions/20924085/python-conversion-between-coordinates
            x = rho * np.cos(phi)
            y = rho * np.sin(phi)
            return x, y


        def radius_at_angle(theta, a, b):
            n = a * b
            d = np.sqrt((a * np.sin(theta)) ** 2 + (b * np.cos(theta)) ** 2)
            return n / d


        from scipy.optimize import NonlinearConstraint
        from scipy import optimize

        POP_SIZE = 10

        data_dict = []

        tissue_masks = [image_thresholded_filtered_closed_ur, image_thresholded_filtered_closed_lr,
                        image_thresholded_filtered_closed_ll, image_thresholded_filtered_closed_ul]
        images = [histo_fragment_ur, histo_fragment_lr, histo_fragment_ll, histo_fragment_ul]
        tissue_masks_closed = [canny_edges_ur, canny_edges_lr, canny_edges_ll, canny_edges_ul]

        N = len(tissue_masks)

        curr_theta = -np.pi
        extra_theta = 2 * np.pi

        N_segments = len(images)
        segment_angle = 2 * np.pi / N_segments

        for i in range(len(tissue_masks)):
            x = tissue_masks[i]
            x_out = tissue_masks_closed[i]
            x = x.copy().astype(np.uint8)
            c = cv2.findContours(x, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)[0]
            x = np.zeros_like(x)
            Mx, My = x.shape
            M = np.maximum(Mx, My)
            hull = cv2.convexHull(c[0])
            cv2.drawContours(x, [hull], -1, 1, -1)
            points = np.stack(np.where(x > 0), axis=1)
            points_out = np.stack(np.where(x_out > 0), axis=1)
            pad = np.maximum(int(M * 0.1), 100)
            initializations = []

            for init_x in [0, Mx / 2, Mx]:
                for init_y in [0, My / 2, My]:
                    initializations.append((init_y, init_x))

            solutions = []
            for init in initializations:
                print("Trying initialization for segment {}: {}".format(i, init))

                bounds = [(0, M), (0, M), (0, M), (0, M),
                          (curr_theta - np.pi / 8, curr_theta + extra_theta),
                          (segment_angle * 0.8, segment_angle * 1.2)]
                x0 = [init[0], init[1], M / 2, M / 2,
                      curr_theta, segment_angle]
                solution = optimize.differential_evolution(
                    circle_arc_loss_cv, x0=x0, bounds=bounds,
                    args=[x, pad], popsize=POP_SIZE, maxiter=250, workers=1)  # updating='immediate'
                solutions.append(solution)

            print([s.fun for s in solutions])
            solution_idx = np.argmin([s.fun for s in solutions])
            solution = solutions[solution_idx]

            cy, cx, r1, r2, theta_1, theta_plus = solution.x
            theta_2 = theta_1 + theta_plus
            curr_theta = theta_1
            extra_theta = theta_plus
            theta = theta_plus
            theta_1_, theta_2_ = np.rad2deg([theta_1, theta_2])
            O = images[i].copy()

            # retrieve points from extremal landmarks
            r_ant = radius_at_angle(theta_1, r1, r2)
            points_cart_ant = np.array([pol2cart(r_ant, theta_1)]) + [cx, cy]
            pca_sorted = np.array([points_cart_ant[0][::-1]])
            point_ant = points_out[
                np.argmin(cdist(points_out, pca_sorted), axis=0)]

            r_pos = radius_at_angle(theta_2, r1, r2)
            points_cart_pos = np.array([pol2cart(r_pos, theta_2)]) + [cx, cy]
            pcp_sorted = np.array([points_cart_pos[0][::-1]])
            point_pos = points_out[
                np.argmin(cdist(points_out, pcp_sorted[::-1]), axis=0)]

            # retrieve points for histogram
            ant_axis_line_mask = np.zeros_like(x, dtype=np.uint8)
            cv2.line(ant_axis_line_mask, [int(cx), int(cy)],
                     np.int32(point_ant[0][::-1]), 1, 80)
            pos_points = np.roll(
                np.array(np.where(ant_axis_line_mask * x_out)).T, 1, 1)

            pos_axis_line_mask = np.zeros_like(x, dtype=np.uint8)
            cv2.line(pos_axis_line_mask, [int(cx), int(cy)],
                     np.int32(point_pos[0][::-1]), 1, 80)
            ant_points = np.roll(
                np.array(np.where(pos_axis_line_mask * x_out)).T, 1, 1)

            # draw examples
            cv2.ellipse(O, (int(cx), int(cy)), (int(r1), int(r2)), angle=0,
                        startAngle=theta_1_, endAngle=theta_2_, color=1,
                        thickness=5)
            cv2.drawMarker(O, [int(cx), int(cy)], [0, 255, 0],
                           markerType=cv2.MARKER_CROSS, thickness=10)

            cv2.drawMarker(O, np.int32(points_cart_ant[0]), [0, 0, 255],
                           markerType=cv2.MARKER_CROSS, thickness=10)
            cv2.drawMarker(O, np.int32(points_cart_pos[0]), [0, 0, 255],
                           markerType=cv2.MARKER_TRIANGLE_UP, thickness=10)

            cv2.line(O, [int(cx), int(cy)], np.int32(point_ant[0][::-1]), [255, 128, 128], 1)
            cv2.line(O, [int(cx), int(cy)], np.int32(point_pos[0][::-1]), [128, 255, 128], 1)

            cv2.drawMarker(O, point_ant[0][::-1], [255, 0, 0],
                           markerType=cv2.MARKER_CROSS, thickness=10)
            cv2.drawMarker(O, point_pos[0][::-1], [255, 0, 0],
                           markerType=cv2.MARKER_TRIANGLE_UP, thickness=10)
            #plt.imshow(O)
            #plt.show()

            data_dict.append({
                "image": images[i],
                "tissue_mask": tissue_masks[i],
                "tissue_mask_closed": tissue_masks_closed[i],
                "quadrant": i,
                "ant_line": np.array([[int(cx), int(cy)], np.int32(point_ant[0][::-1])]),
                "pos_line": np.array([[int(cx), int(cy)], np.int32(point_pos[0][::-1])]),
                "ant_points": ant_points,
                "pos_points": pos_points})

        print(cx, cy)

        ## Calculate histograms and distances between histograms

        # set up functions to calculate colour histograms
        square_size = 64
        n_bins = 32


        def calculate_histogram(image, mask, center, n_bins, size):
            x, y = center
            Mx, My = mask.shape
            x1, x2 = np.maximum(x - size // 2, 0), np.minimum(x + size // 2, Mx)
            y1, y2 = np.maximum(y - size // 2, 0), np.minimum(y + size // 2, My)
            mask = mask[x1:x2, y1:y2]
            sub_image = image[x1:x2, y1:y2]
            sub_image = sub_image.reshape([-1, 3])[mask.reshape([-1]) == 1]

            r_hist = np.histogram(sub_image[:, 0], n_bins, range=[0, 256], density=True)[0]
            g_hist = np.histogram(sub_image[:, 1], n_bins, range=[0, 256], density=True)[0]
            b_hist = np.histogram(sub_image[:, 2], n_bins, range=[0, 256], density=True)[0]

            out = np.concatenate([r_hist, g_hist, b_hist])
            return out


        histograms = []
        print("Calculating histograms for all sections along the x and y edges...")
        for i in range(len(data_dict)):
            data = data_dict[i]
            hx, hy = [], []
            for y, x in data["ant_points"]:
                H = calculate_histogram(
                    data['image'], data['tissue_mask'], [x, y], n_bins, square_size)
                hx.append(H)
            for y, x in data["pos_points"]:
                H = calculate_histogram(
                    data['image'], data['tissue_mask'], [x, y], n_bins, square_size)
                hy.append(H)
            hx = np.array(hx)
            hy = np.array(hy)
            data_dict[i]['histograms_ant'] = hx
            data_dict[i]['histograms_pos'] = hy

        print("Calculating correlation distances between histograms for every tissue section pair...")
        histogram_dists = {}
        for i, j in combinations(range(len(data_dict) + 1), 2):
            i = i % len(data_dict)
            j = j % len(data_dict)
            histogram_dists[i, j] = {
                "ant_pos": cdist(
                    data_dict[i]['histograms_ant'], data_dict[j]['histograms_pos'],
                    metric="correlation"),
                "pos_ant": cdist(
                    data_dict[i]['histograms_pos'], data_dict[j]['histograms_ant'],
                    metric="correlation")}

        # ensuring that max distance == 1
        for i, j in histogram_dists:
            histogram_dists[i, j]['ant_pos'] = np.divide(
                histogram_dists[i, j]['ant_pos'], histogram_dists[i, j]['ant_pos'].max())
            histogram_dists[i, j]['pos_ant'] = np.divide(
                histogram_dists[i, j]['pos_ant'], histogram_dists[i, j]['pos_ant'].max())

        ## Optimization of tissue segment translations and rotations via differential evolution

        POPSIZE = 25  # parameter for the evolutionary optimization (population size)
        MAXITER = 200  # parameter for the evolutionary optimization (population size)

        from skimage.transform import AffineTransform

        from scipy.optimize import NonlinearConstraint
        from scipy import optimize

        np.random.seed(42)

        output_size = max([max(x['image'].shape) for x in data_dict]) * 2
        output_size = [output_size, output_size]
        print('output_size', output_size)


        def par_to_H(theta, tx, ty):
            # converts a set of three parameters to
            # a homography matrix
            H = AffineTransform(
                scale=1, rotation=theta, shear=None, translation=[tx, ty])
            return H.params


        def M_to_quadrant_dict(M, quadrants, anchor):
            H_dict = {}
            Q = [q for q in quadrants if q != anchor]
            for i, q in enumerate(Q):
                H_dict[q] = par_to_H(*[M[i] for i in range(i * 3, i * 3 + 3)])
            return H_dict


        def warp(coords, H):
            out = cv2.perspectiveTransform(
                np.float32(coords[:, np.newaxis, :]), H)[:, 0, :]
            return out


        print("Optimizing tissue mosaic...")


        def loss_fn(M, quadrants, anchor, data_dict, histogram_dists, max_size, alpha=0.1, d=32):
            # M is a list of parameters for homography matrices (every three parameters is
            # converted into a homography matrix). For convenience, I maintain the upper-left
            # quadrant as the fixed image
            # alpha is a scaling factor for the misalignment loss
            hist_loss = 0.
            mis_loss = 0.
            H_dict = M_to_quadrant_dict(M, quadrants, anchor)
            for idx in range(len(data_dict)):
                i, j = idx, (idx + 1) % len(data_dict)
                data1 = data_dict[i]
                data2 = data_dict[j]
                q1 = data1['quadrant']
                q2 = data2['quadrant']

                axis1 = data1['pos_line']
                axis2 = data2['ant_line']
                points1 = data1['pos_points']
                points2 = data2['ant_points']
                hist_dist = histogram_dists[i, j]["pos_ant"]

                if q1 in H_dict and q1 != anchor:
                    axis1 = warp(axis1, H_dict[q1])
                    points1 = warp(points1, H_dict[q1])
                if q2 in H_dict and q2 != anchor:
                    axis2 = warp(axis2, H_dict[q2])
                    points2 = warp(points2, H_dict[q2])
                mis_loss += np.mean((axis1 / max_size - axis2 / max_size) ** 2)
                ss1 = np.random.choice(len(points1),
                                       size=len(points1) // 4,
                                       replace=False)
                ss2 = np.random.choice(len(points2),
                                       size=len(points2) // 4,
                                       replace=False)
                point_distance = cdist(points1[ss1], points2[ss2])
                nx, ny = np.where(point_distance < d)
                nx, ny = ss1[nx], ss2[ny]
                hnb = hist_dist[nx, ny]
                if hnb.size > 0:
                    h = np.mean(hnb)
                else:
                    h = 0.
                # penalty if points have no nearby pixels
                max_dist = hist_dist.max()
                no_nearby_x = point_distance.shape[0] - np.unique(nx).size
                no_nearby_x = no_nearby_x / point_distance.shape[0]
                no_nearby_y = point_distance.shape[1] - np.unique(ny).size
                no_nearby_y = no_nearby_y / point_distance.shape[1]
                hist_loss += h + (no_nearby_x + no_nearby_y) * max_dist
            loss = (mis_loss) * alpha + (1 - alpha) * hist_loss
            return loss


        quadrant_list = list(range(len(data_dict)))
        anchor = len(data_dict) - 1
        bounds = []
        # initialize image positions to the edges where they *should* be
        x0 = []
        a, b, _ = [x['image'] for x in data_dict if x['quadrant'] == anchor][0].shape
        for q in quadrant_list:
            if q != anchor:
                bounds.extend(
                    [(-np.pi / 6, np.pi / 6),
                     (-output_size[0], output_size[0]),
                     (-output_size[0], output_size[0])])

                x0.extend([0, a, b])

        de_result = optimize.differential_evolution(
            loss_fn, bounds, popsize=POPSIZE, maxiter=MAXITER, disp=True, x0=x0,
            mutation=[0.2, 1.0], seed=42,
            args=[quadrant_list, anchor, data_dict, histogram_dists, output_size[0] / 100, 0.1, square_size // 2])

        print(de_result)

        output_size = max([max(x.shape) for x in images_original]) * 2
        output_size = [output_size, output_size]
        output = np.zeros((*output_size, 3), dtype=np.int32)
        output_d = np.zeros((*output_size, 3), dtype=np.int32)

        sc = np.array(
            [[1, 1, DOWNSAMPLE_LEVEL], [1, 1, DOWNSAMPLE_LEVEL], [0, 0, 1]])

        axis_1_final = []
        axis_2_final = []
        H_dict = M_to_quadrant_dict(
            de_result.x, quadrant_list, anchor)
        for i, data in enumerate(data_dict):
            image = images_original[i][:, :, :3]
            sh = image.shape
            mask = resize(data['tissue_mask'], [sh[0], sh[1]], order=0)
            q = data['quadrant']
            if q in H_dict:
                print(q)
                im = cv2.warpPerspective(
                    np.uint8(image * mask[:, :, np.newaxis]),
                    sc * H_dict[q], output_size)
                axis_1_q = data['pos_line']
                axis_1_q = warp(axis_1_q, H_dict[q])
                print("AXIS1", axis_1_q)
                axis_2_q = data['ant_line']
                axis_2_q = warp(axis_2_q, H_dict[q])
                print("AXIS2", axis_2_q)
                axis_1_final.append(axis_1_q)
                axis_2_final.append(axis_2_q)
            else:
                print(q)
                im = cv2.warpPerspective(
                    np.uint8(image * mask[:, :, np.newaxis]),
                    par_to_H(0, 0, 0), output_size)
                axis_1_anchor = data['pos_line']
                axis_1_anchor = warp(axis_1_anchor, par_to_H(0, 0, 0))
                print("AXIS1_anchor", axis_1_anchor)
                axis_2_anchor = data['ant_line']
                axis_2_anchor = warp(axis_2_anchor, par_to_H(0, 0, 0))
                print("AXIS2_anchor", axis_2_anchor)
                axis_1_final.append(axis_1_anchor)
                axis_2_final.append(axis_2_anchor)

            if q in quadrant_list:
                output[im[:, :, :] > 0] += im[im[:, :, :] > 0]
                output_d[im[:, :, :] > 0] += 1

        euclidean_distance_0_1_center = np.sqrt(
            (axis_2_final[1][0][0] - axis_1_final[0][0][0]) ** 2 + (axis_2_final[1][0][1] - axis_1_final[0][0][1]) ** 2)
        euclidean_distance_0_1_out = np.sqrt(
            (axis_2_final[1][1][0] - axis_1_final[0][1][0]) ** 2 + (axis_2_final[1][1][1] - axis_1_final[0][1][1]) ** 2)
        euclidean_distance_1_2_center = np.sqrt(
            (axis_2_final[2][0][0] - axis_1_final[1][0][0]) ** 2 + (axis_2_final[2][0][1] - axis_1_final[1][0][1]) ** 2)
        euclidean_distance_1_2_out = np.sqrt(
            (axis_2_final[2][1][0] - axis_1_final[1][1][0]) ** 2 + (axis_2_final[2][1][1] - axis_1_final[1][1][1]) ** 2)
        euclidean_distance_2_3_center = np.sqrt(
            (axis_2_final[3][0][0] - axis_1_final[2][0][0]) ** 2 + (axis_2_final[3][0][1] - axis_1_final[2][0][1]) ** 2)
        euclidean_distance_2_3_out = np.sqrt(
            (axis_2_final[3][1][0] - axis_1_final[2][1][0]) ** 2 + (axis_2_final[3][1][1] - axis_1_final[2][1][1]) ** 2)
        euclidean_distance_3_0_center = np.sqrt(
            (axis_2_final[0][0][0] - axis_1_final[3][0][0]) ** 2 + (axis_2_final[0][0][1] - axis_1_final[3][0][1]) ** 2)
        euclidean_distance_3_0_out = np.sqrt(
            (axis_2_final[0][1][0] - axis_1_final[3][1][0]) ** 2 + (axis_2_final[0][1][1] - axis_1_final[3][1][1]) ** 2)

        average_euclidean_distance_units = (
                                                       euclidean_distance_0_1_center + euclidean_distance_0_1_out + euclidean_distance_1_2_center
                                                       + euclidean_distance_1_2_out + euclidean_distance_2_3_center + euclidean_distance_2_3_out
                                                       + euclidean_distance_3_0_center + euclidean_distance_3_0_out) / 8

        output[output == 0] = 255
        output = np.where(output_d > 1, output / output_d, output)
        # output[np.sum(output, axis = -1) > 650] = 0
        output = output.astype(np.uint8)

        st.sidebar.image(output, caption="Stitching output", use_column_width=True)
        #imageio.imwrite("/Users/anacastroverde/Desktop/output_black.tif", output, format="tif")

        reader = WSIReader.open(output)
        info_dict = reader.info.as_dict()
        bounds = [0, 0, info_dict['level_dimensions'][0][0] - int(sub_bound_x),
                  info_dict['level_dimensions'][0][1] - int(
                       sub_bound_y)]  # y-550 #To remove the excessive white space around the output image
        region = reader.read_bounds(bounds, resolution=0, units="level", coord_space="resolution")
        #
        #original_spacing = (float(args.original_spacing), float(args.original_spacing))
        # # new_spacing_x = original_size[0]*original_spacing[0]/new_size[0]
        # # new_spacing_y = original_size[1]*original_spacing[1]/new_size[1]
        new_spacing = (2 ** int(level)) * float(original_spacing)  # *(10**(-3))
        #
        tifffile.imwrite(out_path + "output.tif", np.array(region), photometric='rgb', imagej=True,
                         resolution=(1 / new_spacing, 1 / new_spacing), metadata={'spacing': new_spacing, 'unit': 'um'})
        # # imageio.imwrite(args.output_path+"output.tif", output, format="tif")

        average_euclidean_distance_mm = average_euclidean_distance_units * new_spacing * (10 ** (-3))
        #print('Average Euclidean Distance between corner points:', round(average_euclidean_distance_mm, 2),
              #'millimeters')

        end_time = time.time()
        elapsed_time = end_time - start_time
        st.sidebar.metric(label="Average Euclidean Distance (mm)", value=round(average_euclidean_distance_mm, 2), delta=None)
        st.sidebar.metric(label="Total execution time (s)", value=round(elapsed_time, 2), delta=None)
        #print('Total execution time of algorithm:', round(elapsed_time, 2), 'seconds')

