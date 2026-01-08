document.addEventListener('DOMContentLoaded', function() {
    // Элементы формы
    const groupSelect = document.getElementById('group');
    const studentInput = document.getElementById('student');
    const studentIdField = document.getElementById('student_id');
    const currentGroupIdField = document.getElementById('current_group_id');
    const studentSuggestions = document.getElementById('student-suggestions');
    const clearStudentBtn = document.getElementById('clear-student');
    
    // Переменные для сканера
    let studentStream = null;
    let studentScanningInterval = null;
    let studentScannedCodes = new Set();

    // Загрузка групп
    loadGroups();

    // Выбор группы
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

    // Поиск студентов
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

    // Загрузка групп
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

    // === Отправка формы ===
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

            // Количество определяется по кодам
            const codes = Array.from(studentScannedCodes);
            if (codes.length === 0) {
                showError('Прикрепите хотя бы один экземпляр');
                return;
            }

            // Показываем подтверждение
            const confirmMessage = document.getElementById('confirmMessage');
            confirmMessage.textContent = `Вы хотите привязать ${codes.length} книг к своему запросу?`;
            const confirmModal = new bootstrap.Modal(document.getElementById('confirmQuantityModal'));
            confirmModal.show();
        });
    }

    // Подтверждение количества
    document.getElementById('confirmQuantityBtn').addEventListener('click', function() {
        bootstrap.Modal.getInstance(document.getElementById('confirmQuantityModal')).hide(); // Закрываем явно
        const codes = Array.from(studentScannedCodes);
        document.getElementById('copy_codes_hidden').value = codes.join(',');
        document.getElementById('quantity_hidden').value = codes.length;

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
                studentScannedCodes.clear();
                updateStudentAttached();
            } else {
                showError(res.text || 'Ошибка сервера');
            }
        })
        .catch(err => showError('Ошибка отправки: ' + err.message))
        .finally(() => {
            submitBtn.textContent = origText;
            submitBtn.disabled = false;
        });
    });

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
            .catch(err => alert('Ошибка доступа к камере: ' + err));
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
    };

    function updateStudentAttached() {
        const codes = Array.from(studentScannedCodes);
        document.getElementById('studentAttachedCount').textContent = `Прикреплено экземпляров: ${codes.length}`;
        document.getElementById('studentAttachedList').innerHTML = codes.map(c => `<div class="badge bg-success me-1 mb-1">${c}</div>`).join('');
    }

    // Синхронизация ручного ввода
    document.getElementById('manualStudentCodes').addEventListener('input', function() {
        const lines = this.value.trim().split('\n').map(l => l.trim()).filter(l => l);
        studentScannedCodes = new Set(lines);
        updateStudentAttached();
    });

    // Функции ошибок/успеха
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

    document.getElementById('checkStatusBtn').addEventListener('click', function() {
        const el = document.getElementById('requestId');
        const id = el.dataset.fullNumber || '';
        window.location.href = '/check-status?request_id=' + encodeURIComponent(id);
    });
    // Закрытие модального окна сканера с сохранением кодов
    window.closeStudentScanner = function() {
        stopStudentScanner();
        updateMainAttached(); // Обновляем отображение на основной странице
        bootstrap.Modal.getInstance(document.getElementById('qrStudentScannerModal')).hide();
    };

    // Обновление отображения на основной странице
    function updateMainAttached() {
        const codes = Array.from(studentScannedCodes);
        const block = document.getElementById('mainAttachedBlock');
        const countEl = document.getElementById('mainAttachedCount');
        const listEl = document.getElementById('mainAttachedList');

        if (codes.length > 0) {
            block.style.display = 'block';
            countEl.textContent = `Прикреплено экземпляров: ${codes.length}`;
            listEl.innerHTML = codes.map(c => `<div class="badge bg-success me-1 mb-1">${c}</div>`).join('');
        } else {
            block.style.display = 'none';
        }
    }

    // При открытии сканера — восстанавливаем сохранённые коды
    window.openStudentScanner = function() {
        // Синхронизируем коды из textarea (если они уже введены)
        syncCodesFromTextarea();

        // Обновляем отображение
        updateStudentAttached();  // внутри модалки
        updateMainAttached();     // на основной странице

        const modal = new bootstrap.Modal(document.getElementById('qrStudentScannerModal'));
        modal.show();
        startStudentScanner();
    };

    // После сканирования или ручного ввода — обновляем и внутри, и снаружи
    function updateStudentAttached() {
        const codes = Array.from(studentScannedCodes);
        document.getElementById('studentAttachedCount').textContent = `Прикреплено экземпляров: ${codes.length}`;
        document.getElementById('studentAttachedList').innerHTML = codes.map(c => `<div class="badge bg-success me-1 mb-1">${c}</div>`).join('');
        updateMainAttached(); // Синхронизируем с основной страницей
    }

    function syncCodesFromTextarea() {
        const textarea = document.getElementById('manualStudentCodes');
        if (textarea) {
            const lines = textarea.value.trim().split('\n').map(l => l.trim()).filter(l => l);
            studentScannedCodes = new Set(lines);
        }
    }

    // Очистка поля поиска при смене группы
    function loadBooks(groupId) {
        const bookSearchInput = document.getElementById('bookSearch');
        const bookSuggestions = document.getElementById('book-suggestions');
        const bookIdField = document.getElementById('book_id');
        
        if (bookSearchInput) bookSearchInput.value = '';
        if (bookIdField) bookIdField.value = '';
        if (bookSuggestions) {
            bookSuggestions.innerHTML = '';
            bookSuggestions.style.display = 'none';
        }
    }
    // === Поиск книг ===
    const bookSearchInput = document.getElementById('bookSearch');
    const bookSuggestions = document.getElementById('book-suggestions');
    const bookIdField = document.getElementById('book_id');

    if (bookSearchInput) {
        let searchTimeout;

        function renderBookSuggestions(books) {
            bookSuggestions.innerHTML = '';
            // Header with matched count
            const header = document.createElement('div');
            header.className = 'list-group-item list-group-item-light';
            header.textContent = `Найдено: ${books.length}`;
            bookSuggestions.appendChild(header);

            if (books.length === 0) {
                bookSuggestions.innerHTML += '<div class="list-group-item text-muted">Книги не найдены</div>';
            } else {
                books.forEach(b => {
                    const item = document.createElement('button');
                    item.type = 'button';
                    item.className = 'list-group-item list-group-item-action text-start';
                    item.innerHTML = `
                        <strong>${b.name}</strong><br>
                        <small class="text-muted">${b.author} (доступно: ${b.available})</small>
                    `;
                    item.onclick = () => {
                        bookSearchInput.value = b.name;
                        bookIdField.value = b.id;
                        bookSuggestions.style.display = 'none';
                    };
                    bookSuggestions.appendChild(item);
                });
            }
            bookSuggestions.style.display = 'block';
        }

        function doBookSearch(query) {
            const groupId = currentGroupIdField.value;
            if (!groupId) {
                bookSuggestions.innerHTML = '<div class="list-group-item list-group-item-warning">Сначала выберите группу</div>';
                bookSuggestions.style.display = 'block';
                return;
            }

            fetch(`/search-books?q=${encodeURIComponent(query)}&group_id=${groupId}`)
                .then(r => r.json())
                .then(books => renderBookSuggestions(books))
                .catch(err => {
                    console.error(err);
                    bookSuggestions.innerHTML = '<div class="list-group-item text-danger">Ошибка поиска</div>';
                    bookSuggestions.style.display = 'block';
                });
        }

        bookSearchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            const query = this.value.trim();

            searchTimeout = setTimeout(() => doBookSearch(query), 300);
        });

        // Показываем список при фокусе (показываем все книги группы)
        bookSearchInput.addEventListener('focus', function() {
            clearTimeout(searchTimeout);
            doBookSearch('');
        });

        // Скрываем список при клике вне
        document.addEventListener('click', e => {
            if (!bookSearchInput.contains(e.target) && !bookSuggestions.contains(e.target)) {
                bookSuggestions.style.display = 'none';
            }
        });
    }
});