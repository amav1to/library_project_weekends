document.addEventListener('DOMContentLoaded', function() {
    // Элементы формы
    const groupSelect = document.getElementById('group');
    const bookSelect = document.getElementById('book');
    const studentInput = document.getElementById('student');
    const studentIdField = document.getElementById('student_id');
    const currentGroupIdField = document.getElementById('current_group_id');
    const studentSuggestions = document.getElementById('student-suggestions');
    const quantityInput = document.getElementById('quantity');
    const clearStudentBtn = document.getElementById('clear-student');

    // Переменные для сканера экземпляров у студента
    let studentStream = null;
    let studentScanningInterval = null;
    let studentScannedCodes = new Set();

    // === Сканер экземпляров для студента ===
    window.openStudentScanner = function() {
        const quantity = parseInt(quantityInput.value) || 1;
        document.getElementById('studentAttachedCount').textContent = `Прикреплено экземпляров: 0 из ${quantity}`;
        studentScannedCodes.clear();
        document.getElementById('studentAttachedList').innerHTML = '';
        document.getElementById('manualStudentCodes').value = '';

        const modal = new bootstrap.Modal(document.getElementById('qrStudentScannerModal'));
        modal.show();
        startStudentScanner();
    };

    function startStudentScanner() {
        navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
            .then(stream => {
                studentStream = stream;
                const video = document.getElementById('qr-student-video');
                video.srcObject = stream;
                video.play();

                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d');

                studentScanningInterval = setInterval(() => {
                    if (video.readyState === video.HAVE_ENOUGH_DATA) {
                        canvas.height = video.videoHeight;
                        canvas.width = video.videoWidth;
                        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
                        const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                        const code = jsQR(imageData.data, imageData.width, imageData.height);

                        if (code) {
                            const codeVal = code.data.trim();
                            if (!studentScannedCodes.has(codeVal)) {
                                studentScannedCodes.add(codeVal);
                                const textarea = document.getElementById('manualStudentCodes');
                                textarea.value += (textarea.value ? '\n' : '') + codeVal;
                                updateStudentAttached();
                            }
                        }
                    }
                }, 300);
            })
            .catch(err => {
                console.error('Ошибка камеры:', err);
                alert('Не удалось получить доступ к камере. Проверьте разрешения.');
            });
    }

    window.stopStudentScanner = function() {
        if (studentStream) {
            studentStream.getTracks().forEach(t => t.stop());
            studentStream = null;
        }
        if (studentScanningInterval) {
            clearInterval(studentScanningInterval);
            studentScanningInterval = null;
        }
        const video = document.getElementById('qr-student-video');
        if (video) video.srcObject = null;
    }

    function updateStudentAttached() {
        const quantity = parseInt(quantityInput.value) || 1;
        const codes = Array.from(studentScannedCodes);
        document.getElementById('studentAttachedCount').textContent = `Прикреплено экземпляров: ${codes.length} из ${quantity}`;
        document.getElementById('studentAttachedList').innerHTML = codes.map(c => `<div class="badge bg-success me-1 mb-1">${c}</div>`).join('');
    }

    // Синхронизация textarea
    const manualCodesTextarea = document.getElementById('manualStudentCodes');
    if (manualCodesTextarea) {
        manualCodesTextarea.addEventListener('input', function() {
            const lines = this.value.trim().split('\n').map(l => l.trim()).filter(l => l);
            studentScannedCodes = new Set(lines);
            updateStudentAttached();
        });
    }

    // Обновление счётчика при изменении количества
    if (quantityInput) {
        quantityInput.addEventListener('change', updateStudentAttached);
    }

    // 1. Загрузка групп
    function loadGroups() {
        fetch('/get-groups')
            .then(r => r.json())
            .then(groups => {
                groupSelect.innerHTML = '<option value="">-- Выберите группу --</option>';
                groups.forEach(g => {
                    const opt = document.createElement('option');
                    opt.value = g.id;
                    opt.textContent = g.name;
                    groupSelect.appendChild(opt);
                });
            })
            .catch(err => {
                console.error(err);
                groupSelect.innerHTML = '<option value="">Ошибка загрузки групп</option>';
            });
    }
    loadGroups();

    // 2. Выбор группы
    if (groupSelect) {
        groupSelect.addEventListener('change', function() {
            const groupId = this.value;
            currentGroupIdField.value = groupId;
            if (groupId) {
                loadBooks(groupId);
                studentInput.value = '';
                studentIdField.value = '';
            } else {
                bookSelect.innerHTML = '<option value="">-- Сначала выберите группу --</option>';
                studentSuggestions.style.display = 'none';
                studentSuggestions.innerHTML = '';
                currentGroupIdField.value = '';
            }
        });
    }

    // 3. Загрузка книг
    function loadBooks(groupId) {
        fetch(`/get-books/${groupId}`)
            .then(r => r.json())
            .then(books => {
                bookSelect.innerHTML = '<option value="">-- Выберите книгу --</option>';
                if (books.length === 0) {
                    bookSelect.innerHTML += '<option value="">Нет доступных книг</option>';
                    return;
                }
                books.forEach(b => {
                    const opt = document.createElement('option');
                    opt.value = b.id;
                    opt.textContent = `${b.name} (доступно: ${b.available})`;
                    bookSelect.appendChild(opt);
                });

                // Ограничение количества
                bookSelect.addEventListener('change', function() {
                    const match = this.selectedOptions[0].text.match(/доступно:\s*(\d+)/);
                    if (match && quantityInput) {
                        const max = parseInt(match[1]);
                        quantityInput.max = max;
                        if (parseInt(quantityInput.value) > max) quantityInput.value = max;
                        updateStudentAttached();
                    }
                });
            })
            .catch(err => {
                console.error(err);
                bookSelect.innerHTML = '<option value="">Ошибка загрузки книг</option>';
            });
    }

    // 4. Поиск студентов
    if (studentInput) {
        let timeout;
        studentInput.addEventListener('input', function() {
            clearTimeout(timeout);
            const query = this.value.trim();
            const groupId = currentGroupIdField.value;
            if (!groupId) {
                showMessage('Сначала выберите группу');
                return;
            }
            if (query === '') {
                loadAllStudents(groupId);
                return;
            }
            timeout = setTimeout(() => searchStudents(query, groupId), 200);
        });

        document.addEventListener('click', e => {
            if (!studentInput.contains(e.target) && !studentSuggestions.contains(e.target)) {
                studentSuggestions.style.display = 'none';
            }
        });

        studentInput.addEventListener('click', () => {
            const groupId = currentGroupIdField.value;
            if (groupId) loadAllStudents(groupId);
        });
    }

    function loadAllStudents(groupId) {
        fetch(`/get-students/${groupId}`)
            .then(r => r.json())
            .then(students => updateStudentSuggestions(students, 'Студенты группы:'))
            .catch(() => showMessage('Ошибка загрузки студентов'));
    }

    function searchStudents(query, groupId) {
        fetch(`/search-students?q=${encodeURIComponent(query)}&group_id=${groupId}`)
            .then(r => r.json())
            .then(students => updateStudentSuggestions(students, `Результаты поиска "${query}":`))
            .catch(() => showMessage('Ошибка поиска'));
    }

    function updateStudentSuggestions(students, title) {
        studentSuggestions.innerHTML = '';
        if (students.length === 0) {
            studentSuggestions.innerHTML = '<div class="list-group-item text-muted">Студенты не найдены</div>';
        } else {
            studentSuggestions.innerHTML += `<div class="list-group-item list-group-item-light">${title}</div>`;
            students.forEach(s => {
                const btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'list-group-item list-group-item-action';
                btn.textContent = s.name;
                btn.dataset.studentId = s.id;
                btn.addEventListener('click', () => {
                    studentInput.value = s.name;
                    studentIdField.value = s.id;
                    studentSuggestions.style.display = 'none';
                });
                studentSuggestions.appendChild(btn);
            });
        }
        studentSuggestions.style.display = 'block';
    }

    function showMessage(msg) {
        studentSuggestions.innerHTML = `<div class="list-group-item list-group-item-warning">${msg}</div>`;
        studentSuggestions.style.display = 'block';
    }
    
    // Очистка студента
    if (clearStudentBtn) {
        clearStudentBtn.addEventListener('click', () => {
            studentInput.value = '';
            studentIdField.value = '';
            studentSuggestions.style.display = 'none';
        });
    }

    // === Отправка формы (обновлённая с модальным окном ошибок) ===
    const form = document.getElementById('bookRequestForm');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();

            // Проверка студента
            if (!studentInput.value.trim()) {
                showError('Введите ФИО студента');
                return;
            }
            if (!studentIdField.value) {
                showError('Выберите студента из списка');
                return;
            }

            // Проверка экземпляров
            const quantity = parseInt(quantityInput.value) || 1;
            const codes = Array.from(studentScannedCodes);

            if (codes.length !== quantity) {
                let word = 'экземпляров';
                if (quantity === 1) word = 'экземпляр';
                else if ([2, 3, 4].includes(quantity % 10) && !(quantity % 100 >= 11 && quantity % 100 <= 14)) word = 'экземпляра';

                showError(`Вы должны прикрепить ровно ${quantity} ${word} (сейчас: ${codes.length})`);
                return;
            }

            // Заполняем скрытое поле
            document.getElementById('copy_codes_hidden').value = codes.join(',');

            const submitBtn = form.querySelector('button[type="submit"]');
            const origText = submitBtn.textContent;
            submitBtn.textContent = 'Отправка...';
            submitBtn.disabled = true;

            fetch('/request-book', {
                method: 'POST',
                body: new FormData(form)
            })
            .then(r => r.text().then(text => ({ ok: r.ok, text })))
            .then(res => {
                if (res.ok) {
                    showSuccessModal(res.text);
                    form.reset();
                    studentIdField.value = '';
                    currentGroupIdField.value = '';
                    studentScannedCodes.clear();
                    updateStudentAttached();
                    // Скрываем возможные открытые модалки ошибок
                    bootstrap.Modal.getInstance(document.getElementById('errorModal'))?.hide();
                } else {
                    showError(res.text || 'Произошла неизвестная ошибка на сервере');
                }
            })
            .catch(err => {
                showError('Ошибка отправки запроса: ' + err.message);
            })
            .finally(() => {
                submitBtn.textContent = origText;
                submitBtn.disabled = false;
            });
        });
    }

    function showError(msg) {
        const errorModalBody = document.getElementById('errorModalBody');
        if (errorModalBody) {
            errorModalBody.textContent = msg;
        }
        const errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
        errorModal.show();
    }

    function showSuccessModal(message) {
        const match = message.match(/#(\d+)/);
        if (match) {
            const id = match[1];
            const el = document.getElementById('requestId');
            if (el) {
                el.textContent = id;
                el.dataset.fullNumber = id;
            }
            new bootstrap.Modal(document.getElementById('successModal')).show();
        } else {
            alert(message);
        }
    }

    // Кнопка "Проверить статус" в модальном окне успеха
    document.getElementById('checkStatusBtn')?.addEventListener('click', function() {
        const el = document.getElementById('requestId');
        const id = el?.dataset.fullNumber || '';
        window.location.href = '/check-status?request_id=' + encodeURIComponent(id);
    });

    // === Кнопки + и - для количества экземпляров ===
    const decreaseBtn = document.getElementById('decrease-quantity');
    const increaseBtn = document.getElementById('increase-quantity');

    if (quantityInput && decreaseBtn && increaseBtn) {
        // Увеличиваем
        increaseBtn.addEventListener('click', function() {
            let value = parseInt(quantityInput.value) || 1;
            quantityInput.value = value + 1;
            updateStudentAttached(); // Обновляем текст "Прикреплено: X из Y"
        });

        // Уменьшаем (не ниже 1)
        decreaseBtn.addEventListener('click', function() {
            let value = parseInt(quantityInput.value) || 1;
            if (value > 1) {
                quantityInput.value = value - 1;
                updateStudentAttached();
            }
        });

        // Если пользователь вручную меняет значение в поле
        quantityInput.addEventListener('change', function() {
            let value = parseInt(this.value) || 1;
            if (value < 1) {
                this.value = 1;
            }
            updateStudentAttached();
        });

        // При загрузке страницы тоже обновляем счётчик
        updateStudentAttached();
    }
});