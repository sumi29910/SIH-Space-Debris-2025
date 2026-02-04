// Global variables
let capturedImage = null;
let sampleImages = [];
let debrisCount = 12000;
let objectCount = 1000;

// DOM elements
const video = document.getElementById('video');
const startCameraBtn = document.getElementById('start-camera');
const captureBtn = document.getElementById('capture-btn');
const imageUpload = document.getElementById('image-upload');
const uploadedPreview = document.getElementById('uploaded-preview');
const resultCanvas = document.getElementById('result-canvas');
const detectionStatus = document.getElementById('detection-status');
const debrisIdElement = document.getElementById('debris-id');
const processBtn = document.getElementById('process-btn');
const resetBtn = document.getElementById('reset-btn');

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    loadSampleImages();
    setupEventListeners();
});

// Load sample images from the directory
async function loadSampleImages() {
    // In a real implementation, this would fetch images from the server
    // For now, we'll simulate by creating sample image objects
    const imageNames = [
        'Screenshot 2025-12-09 191011.png',
        'Screenshot 2025-12-09 191023.png',
        'Screenshot 2025-12-09 191030.png',
        'Screenshot 2025-12-09 191037.png',
        'Screenshot 2025-12-09 191042.png',
        'Screenshot 2025-12-09 191058.png',
        'Screenshot 2025-12-09 191104.png',
        'Screenshot 2025-12-09 191109.png'
    ];
    
    // Load each image and preprocess it
    for (const name of imageNames) {
        const img = new Image();
        img.crossOrigin = "Anonymous"; // Handle potential CORS issues
        img.src = name;
        
        // Wait for image to load before preprocessing
        await new Promise((resolve) => {
            img.onload = () => {
                console.log(`Loaded sample image: ${name}`);
                
                // Preprocess the image to remove white background
                const canvas = document.createElement('canvas');
                canvas.width = img.width || 640;
                canvas.height = img.height || 480;
                const ctx = canvas.getContext('2d');
                
                // Draw the image on the canvas
                ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                
                // Remove white background
                removeBackground(canvas);
                
                // Update the image source with processed data
                img.src = canvas.toDataURL('image/png');
                resolve();
            };
            
            // Handle image loading errors
            img.onerror = () => {
                console.error(`Failed to load sample image: ${name}`);
                resolve(); // Continue with other images
            };
        });
        
        sampleImages.push(img);
    }
}

// Set up event listeners
function setupEventListeners() {
    startCameraBtn.addEventListener('click', startCamera);
    captureBtn.addEventListener('click', captureImage);
    imageUpload.addEventListener('change', handleImageUpload);
    processBtn.addEventListener('click', processImage);
    resetBtn.addEventListener('click', resetApp);
}

// Start camera functionality
async function startCamera() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true });
        video.srcObject = stream;
    } catch (err) {
        console.error('Error accessing camera:', err);
        alert('Could not access the camera. Please ensure you have granted permission.');
    }
}

// Capture image from camera
function captureImage() {
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    capturedImage = new Image();
    capturedImage.src = canvas.toDataURL('image/png');
    
    // Stop the camera stream
    const stream = video.srcObject;
    if (stream) {
        const tracks = stream.getTracks();
        tracks.forEach(track => track.stop());
    }
    
    // Display the captured image in the preview
    uploadedPreview.innerHTML = '';
    const imgElement = document.createElement('img');
    imgElement.src = capturedImage.src;
    uploadedPreview.appendChild(imgElement);
    
    // Also set the captured image as the source for processing
    resultCanvas.width = canvas.width;
    resultCanvas.height = canvas.height;
    const resultCtx = resultCanvas.getContext('2d');
    resultCtx.drawImage(canvas, 0, 0);
}

// Handle image upload
function handleImageUpload(event) {
    const file = event.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            capturedImage = new Image();
            capturedImage.src = e.target.result;
            
            capturedImage.onload = function() {
                // Display uploaded image in preview
                uploadedPreview.innerHTML = '';
                const imgElement = document.createElement('img');
                imgElement.src = capturedImage.src;
                uploadedPreview.appendChild(imgElement);
                
                // Draw image on result canvas
                resultCanvas.width = capturedImage.width;
                resultCanvas.height = capturedImage.height;
                const ctx = resultCanvas.getContext('2d');
                ctx.drawImage(capturedImage, 0, 0);
            };
        };
        reader.readAsDataURL(file);
    }
}

// Process the image to detect debris
function processImage() {
    if (!capturedImage) {
        alert('Please capture or upload an image first.');
        return;
    }
    
    // Remove background from the captured image
    removeBackground(resultCanvas);
    
    // Perform debris detection
    detectDebris();
}

// Remove background from image
function removeBackground(canvas) {
    const ctx = canvas.getContext('2d');
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const data = imageData.data;
    
    // Improved background removal algorithm
    for (let i = 0; i < data.length; i += 4) {
        const r = data[i];
        const g = data[i + 1];
        const b = data[i + 2];
        const alpha = data[i + 3];
        
        // Calculate luminance to identify white-like pixels
        const luminance = 0.299 * r + 0.587 * g + 0.114 * b;
        
        // Check if the pixel is close to white and bright
        if (luminance > 200 && r > 200 && g > 200 && b > 200) {
            // Make the pixel transparent
            data[i + 3] = 0; // Alpha channel
        }
        // Additional check for near-white pixels
        else if (luminance > 230) {
            // Reduce alpha for near-white pixels to create smooth transition
            const newAlpha = Math.max(0, alpha * (1 - (luminance - 230) / 25));
            data[i + 3] = newAlpha;
        }
    }
    
    ctx.putImageData(imageData, 0, 0);
}

// Preprocess sample images to remove white backgrounds
function preprocessSampleImages() {
    sampleImages.forEach((img, index) => {
        // Create a temporary canvas to process the image
        const canvas = document.createElement('canvas');
        canvas.width = img.width || 640;
        canvas.height = img.height || 480;
        const ctx = canvas.getContext('2d');
        
        // Draw the image on the canvas
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        
        // Remove white background
        removeBackground(canvas);
        
        // Update the image source with processed data
        img.src = canvas.toDataURL('image/png');
    });
}

// Detect debris by matching with sample images
function detectDebris() {
    // Show processing status with spinner
    detectionStatus.innerHTML = '<span class="processing-spinner"></span> Processing...';
    detectionStatus.className = ''; // Reset any previous classes
    
    setTimeout(() => {
        // Perform image comparison with sample images
        const matchResult = compareWithSamples();
        
        if (matchResult.isMatch) {
            // Generate debris ID
            const debrisId = `DEB ${debrisCount}`;
            debrisCount++;
            
            detectionStatus.textContent = 'Recognition passed: Debris detected';
            detectionStatus.className = 'status-debris'; // Add debris class for styling
            debrisIdElement.textContent = `ID: ${debrisId}`;
        } else {
            // Generate object ID
            const objectId = `OBJ ${objectCount}`;
            objectCount++;
            
            detectionStatus.textContent = 'Debris not detected';
            detectionStatus.className = 'status-object'; // Add object class for styling
            debrisIdElement.textContent = `ID: ${objectId}`;
        }
    }, 2000); // Simulate 2 seconds processing time
}

// Compare captured image with sample images based on physical appearance
function compareWithSamples() {
    // Get the image data from the result canvas (processed captured image)
    const resultCtx = resultCanvas.getContext('2d');
    const capturedData = resultCtx.getImageData(0, 0, resultCanvas.width, resultCanvas.height);
    
    // Compare with each sample image
    for (let i = 0; i < sampleImages.length; i++) {
        const sampleImg = sampleImages[i];
        
        // Create a temporary canvas for the sample image
        const sampleCanvas = document.createElement('canvas');
        sampleCanvas.width = resultCanvas.width;
        sampleCanvas.height = resultCanvas.height;
        const sampleCtx = sampleCanvas.getContext('2d');
        
        // Draw the sample image to match the size of the captured image
        sampleCtx.drawImage(sampleImg, 0, 0, sampleCanvas.width, sampleCanvas.height);
        
        // Get the image data for the sample
        const sampleData = sampleCtx.getImageData(0, 0, sampleCanvas.width, sampleCanvas.height);
        
        // Calculate similarity based on physical appearance (shape, form)
        const similarity = calculateAppearanceSimilarity(capturedData, sampleData);
        
        // If similarity is above threshold, consider it a match
        if (similarity > 0.5) { // 50% similarity threshold for faster matching
            return { isMatch: true, similarity: similarity };
        }
    }
    
    return { isMatch: false, similarity: 0 };
}

// Calculate similarity based on physical appearance (shape, form)
function calculateAppearanceSimilarity(imgData1, imgData2) {
    // Ensure both images have the same dimensions
    if (imgData1.width !== imgData2.width || imgData1.height !== imgData2.height) {
        return 0;
    }
    
    const data1 = imgData1.data;
    const data2 = imgData2.data;
    const width = imgData1.width;
    const height = imgData1.height;
    
    // Create simplified representations of the images focusing on shape
    const shape1 = extractShapeFeatures(data1, width, height);
    const shape2 = extractShapeFeatures(data2, width, height);
    
    // Compare shapes using a faster algorithm
    const shapeSimilarity = compareShapes(shape1, shape2);
    
    return shapeSimilarity;
}

// Extract basic shape features from image data
function extractShapeFeatures(data, width, height) {
    // Create a simplified grid representation of the image
    const gridSize = 16; // 16x16 grid
    const cellWidth = Math.floor(width / gridSize);
    const cellHeight = Math.floor(height / gridSize);
    
    const grid = new Array(gridSize * gridSize).fill(0);
    
    // Sample the image in a grid pattern to extract shape features
    for (let y = 0; y < gridSize; y++) {
        for (let x = 0; x < gridSize; x++) {
            let cellFilled = 0;
            const startY = y * cellHeight;
            const startX = x * cellWidth;
            
            // Count filled pixels in this grid cell
            for (let cy = 0; cy < cellHeight; cy++) {
                for (let cx = 0; cx < cellWidth; cx++) {
                    const idx = ((startY + cy) * width + (startX + cx)) * 4;
                    if (idx < data.length && data[idx + 3] > 128) { // Alpha channel > 128 means visible
                        cellFilled++;
                    }
                }
            }
            
            // Normalize the fill value for this cell
            const totalPixels = cellWidth * cellHeight;
            grid[y * gridSize + x] = totalPixels > 0 ? cellFilled / totalPixels : 0;
        }
    }
    
    return grid;
}

// Compare two shape feature arrays
function compareShapes(shape1, shape2) {
    if (shape1.length !== shape2.length) {
        return 0;
    }
    
    let similaritySum = 0;
    let comparisonCount = 0;
    
    // Compare each grid cell
    for (let i = 0; i < shape1.length; i++) {
        // Only compare cells that have significant content
        if (shape1[i] > 0.1 || shape2[i] > 0.1) {
            // Calculate similarity between corresponding cells
            const diff = Math.abs(shape1[i] - shape2[i]);
            similaritySum += (1 - diff);
            comparisonCount++;
        }
    }
    
    // Return average similarity
    return comparisonCount > 0 ? similaritySum / comparisonCount : 0;
}

// Reset the application
function resetApp() {
    // Reset video stream if active
    const stream = video.srcObject;
    if (stream) {
        const tracks = stream.getTracks();
        tracks.forEach(track => track.stop());
    }
    
    // Reset UI elements
    video.srcObject = null;
    uploadedPreview.innerHTML = '';
    resultCanvas.getContext('2d').clearRect(0, 0, resultCanvas.width, resultCanvas.height);
    detectionStatus.textContent = 'Ready to scan...';
    detectionStatus.style.color = 'black';
    debrisIdElement.textContent = 'ID: -';
    imageUpload.value = '';
    capturedImage = null;
}