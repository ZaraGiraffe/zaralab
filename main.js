const { app, BrowserWindow } = require('electron');
const path = require('path');
const { exec } = require('child_process');

function createWindow() {
    const win = new BrowserWindow({
        width: 1200,
        height: 800,
        webPreferences: {
            preload: path.join(__dirname, 'preload.js'),
            nodeIntegration: true,
            contextIsolation: false
        }
    });

    setTimeout(() => {
        win.loadURL('http://127.0.0.1:5000');
    }, 2000);
}

app.whenReady().then(() => {
    exec('python app.py', {
        cwd: __dirname 
    }, (err, stdout, stderr) => {
        if (err) {
            console.error(`Error starting Flask: ${err}`);
            return;
        }
        console.log(stdout);
    });

    createWindow();

    app.on('activate', function () {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});

app.on('window-all-closed', function () {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});
