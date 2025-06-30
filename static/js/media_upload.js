document.addEventListener('DOMContentLoaded', () => {
  const dropArea = document.getElementById('drop-area');
  if (!dropArea) return;
  dropArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropArea.classList.add('dragover');
  });
  dropArea.addEventListener('dragleave', () => {
    dropArea.classList.remove('dragover');
  });
  dropArea.addEventListener('drop', (e) => {
    e.preventDefault();
    dropArea.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (!files.length) return;
    const progress = document.getElementById('upload-progress');
    const progressBar = progress ? progress.querySelector('.progress-bar') : null;
    const messageEl = document.getElementById('upload-message');
    const athleteId = dropArea.dataset.athleteId;

    const uploadFile = (file) => {
      return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        xhr.open('POST', `/api/athletes/${athleteId}/media`);

        xhr.upload.addEventListener('progress', (ev) => {
          if (ev.lengthComputable && progressBar) {
            const pct = (ev.loaded / ev.total) * 100;
            progressBar.style.width = pct + '%';
          }
        });

        xhr.onload = () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            resolve();
          } else {
            reject(new Error('Upload failed'));
          }
        };
        xhr.onerror = () => reject(new Error('Upload failed'));

        const formData = new FormData();
        formData.append('file', file);
        xhr.send(formData);
      });
    };

    const run = async () => {
      for (const file of files) {
        if (progress && progressBar) {
          progress.classList.remove('d-none');
          progressBar.style.width = '0%';
        }
        if (messageEl) messageEl.textContent = `Uploading ${file.name}...`;
        try {
          await uploadFile(file);
          if (messageEl) messageEl.textContent = `${file.name} uploaded successfully.`;
        } catch (err) {
          if (messageEl) messageEl.textContent = `Error uploading ${file.name}`;
        }
      }
      setTimeout(() => {
        if (progress) progress.classList.add('d-none');
      }, 1000);
    };

    run();
  });
});
