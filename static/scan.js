Webcam.set({
    width: 1080,
    height: 810,
    image_format: 'jpeg',
    jpeg_quality: 90,
    constraints: {
        facingMode: 'environment'
    }
});
Webcam.attach('#my_camera');
function take_snapshot() {
    Webcam.snap(function (data_uri) {
        const width = 1080;
        const height = 810;

        const image = document.createElement("img");
        image.src = data_uri;
        image.setAttribute("crossOrigin", "");

        const canvas = document.createElement("canvas");
        canvas.width = width;
        canvas.height = height;

        const context = canvas.getContext("2d");

        if (context) {
            image.onload = function () {
                context.drawImage(image, 0, 0, width, height);
                const pixels = context.getImageData(0, 0, width, height);
                const imageData = pixels.data;
                const code = jsQR(imageData, width, height);

                if (code) {
                    document.getElementById("results").innerHTML += '&nbsp<h2>Found QRcode!</h2>';
                    window.location.href = "/manage/" + code.data;
                } else {
                    document.getElementById("results").innerHTML += '&nbsp<h2>Code Not Found. Try Again.</h2>';
                }
            };
        }
        document.getElementById("results").innerHTML = '<img src="' + data_uri + '" width="320" height="240"/>';
    });
}
