document.addEventListener('DOMContentLoaded', function() {
    // Toggle dark mode
    const themeToggleButton = document.getElementById('theme-toggle');
    if (themeToggleButton) {
        // Controlla se la modalità scura è stata precedentemente attivata
        if (localStorage.getItem('dark-mode') === 'true') {
            document.body.classList.add('dark-mode');
        }

        themeToggleButton.addEventListener('click', function() {
            document.body.classList.toggle('dark-mode');

            // Aggiorna localStorage in base allo stato attuale
            if (document.body.classList.contains('dark-mode')) {
                localStorage.setItem('dark-mode', 'true');
            } else {
                localStorage.setItem('dark-mode', 'false');
            }
        });
    }

    // Handle form submission
    const form = document.getElementById('process-form');
    const submitButton = document.getElementById('process-button');
    const resultDiv = document.getElementById('result');
    const resultMessage = document.getElementById('result-message');
    const resultOutput = document.getElementById('result-output');

    if (form) {
        form.addEventListener('submit', function(event) {
            event.preventDefault(); // Prevent default submission

            // Disable the submit button
            submitButton.disabled = true;
            submitButton.textContent = 'Processing...';

            const formData = new FormData(form);

            // If audio recording is selected, append the audio blob
            if (processType === 'audio' && recordedAudioBlob) {
                formData.append('audio_file', recordedAudioBlob, 'recording.webm');
            }

            fetch(form.action, {
                method: 'POST',
                body: formData
            })
            .then(response => response.text())
            .then(html => {
                // Replace current page's HTML with response
                document.open();
                document.write(html);
                document.close();
            })
            .catch(error => {
                console.error('Error:', error);
                resultDiv.classList.remove('is-hidden');
                resultMessage.textContent = 'An error occurred while processing. Please try again later.';
                resultOutput.textContent = '';
            })
            .finally(() => {
                // Re-enable the submit button
                submitButton.disabled = false;
                submitButton.textContent = 'Process';
            });
        });
    }

    // Hide result notification when close button is clicked
    if (resultDiv) {
        const closeButton = document.querySelector('#result .delete');
        if (closeButton) {
            closeButton.addEventListener('click', function() {
                resultDiv.classList.add('is-hidden');
            });
        }
    }

    // Toggle between process types
    const webSearchOptions = document.getElementById('web-search-options');
    const fileUploadOption = document.getElementById('file-upload-option');
    const audioRecordingOption = document.getElementById('audio-recording-option');
    const processTypeInputs = document.querySelectorAll('input[name="process_type"]');
    const fileInput = document.querySelector('#file-upload-option input[type="file"]');
    let processType = 'web'; // default process type

    processTypeInputs.forEach(input => {
        input.addEventListener('change', function() {
            processType = this.value;

            if (this.value === 'web') {
                webSearchOptions.style.display = 'block';
                fileUploadOption.style.display = 'none';
                audioRecordingOption.style.display = 'none';
                fileInput.removeAttribute('required');
            } else if (this.value === 'file') {
                webSearchOptions.style.display = 'none';
                fileUploadOption.style.display = 'block';
                audioRecordingOption.style.display = 'none';
                fileInput.setAttribute('required', '');
            } else if (this.value === 'audio') {
                webSearchOptions.style.display = 'none';
                fileUploadOption.style.display = 'none';
                audioRecordingOption.style.display = 'block';
                fileInput.removeAttribute('required');
            }
        });
    });

    // Ensure correct initial state
    const initialProcessType = document.querySelector('input[name="process_type"]:checked');
    if (initialProcessType) {
        processType = initialProcessType.value;
        processTypeInputs.forEach(input => input.dispatchEvent(new Event('change')));
    }

    // Audio Recording Functionality
    let mediaRecorder;
    let recordedChunks = [];
    let recordedAudioBlob = null;
    const recordButton = document.getElementById('record-button');
    const recordingStatus = document.getElementById('recording-status');

    if (recordButton) {
        let isRecording = false;

        recordButton.addEventListener('click', function() {
            if (!isRecording) {
                // Start recording
                navigator.mediaDevices.getUserMedia({ audio: true })
                    .then(function(stream) {
                        mediaRecorder = new MediaRecorder(stream);
                        mediaRecorder.start();
                        isRecording = true;
                        recordButton.textContent = 'Stop Recording';
                        recordingStatus.textContent = 'Recording...';

                        recordedChunks = [];

                        mediaRecorder.addEventListener('dataavailable', function(e) {
                            if (e.data.size > 0) {
                                recordedChunks.push(e.data);
                            }
                        });

                        mediaRecorder.addEventListener('stop', function() {
                            recordedAudioBlob = new Blob(recordedChunks, { type: 'audio/webm' });
                            recordingStatus.textContent = 'Recording stopped.';
                        });
                    })
                    .catch(function(err) {
                        console.error('Error accessing microphone: ' + err);
                        alert('Error accessing microphone: ' + err.message);
                    });
            } else {
                // Stop recording
                mediaRecorder.stop();
                isRecording = false;
                recordButton.textContent = 'Start Recording';
                recordingStatus.textContent = 'Processing audio...';
            }
        });
    }

    // Search Engine Management
    const searchEnginesContainer = document.getElementById('search-engines');
    const addSearchEngineButton = document.getElementById('add-search-engine');

    if (searchEnginesContainer && addSearchEngineButton) {
        function createSearchEngineEntry(name = '', url = '') {
            const entry = document.createElement('div');
            entry.className = 'field has-addons search-engine-entry';
            entry.innerHTML = `
                <div class="control">
                    <input class="input" type="text" name="search_engine_name[]" value="${name}" placeholder="Name" required>
                </div>
                <div class="control">
                    <input class="input" type="text" name="search_engine_url[]" value="${url}" placeholder="URL" required>
                </div>
                <div class="control">
                    <button type="button" class="button is-danger remove-search-engine">Remove</button>
                </div>
            `;
            return entry;
        }

        // Add a new search engine entry
        addSearchEngineButton.addEventListener('click', function() {
            const newEntry = createSearchEngineEntry();
            searchEnginesContainer.appendChild(newEntry);
        });

        // Remove a search engine entry
        searchEnginesContainer.addEventListener('click', function(e) {
            if (e.target.classList.contains('remove-search-engine')) {
                const entry = e.target.closest('.search-engine-entry');
                if (entry) {
                    entry.remove();
                }
            }
        });

        // Prevent form submission if there are no search engines
        const configForm = document.getElementById('config-form');
        if (configForm) {
            configForm.addEventListener('submit', function(e) {
                const searchEngineEntries = searchEnginesContainer.querySelectorAll('.search-engine-entry');
                if (searchEngineEntries.length === 0) {
                    e.preventDefault();
                    alert('Please add at least one search engine.');
                }
            });
        }
    }

});

// Funzione per il toggle dell'anteprima dei file
function togglePreview(file) {
    const previewDiv = document.getElementById(`preview-${file}`);
    if (previewDiv) {
        previewDiv.style.display = previewDiv.style.display === 'none' ? 'block' : 'none';
    }
}
