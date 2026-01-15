document.addEventListener('DOMContentLoaded', function() {
    // Элементы формы
    const groupInput = document.getElementById('groupInput');
    const groupSuggestions = document.getElementById('group-suggestions');
    let groupsList = [];
    // availableCopies holds copy_code strings (in numeric order) for the currently selected book
    let availableCopies = [];
    const studentInput = document.getElementById('student');
    const studentIdField = document.getElementById('student_id');
    const currentGroupIdField = document.getElementById('current_group_id');
    const groupIdHiddenField = document.getElementById('group_id_hidden');
    const studentSuggestions = document.getElementById('student-suggestions');
    const clearStudentBtn = document.getElementById('clear-student');
    
    // Переменные для сканера
    let studentStream = null;
    let studentScanningInterval = null;
    let studentScannedCodes = new Set();

    // Загрузка групп
    loadGroups();

    // Выбор/поиск группы
    function renderGroupSuggestions(groups, header) {
        groupSuggestions.innerHTML = '';
        if (!groups || groups.length === 0) {
            groupSuggestions.innerHTML = '<div class="list-group-item text-muted">Группы не найдены</div>';
        } else {
            if (header) groupSuggestions.innerHTML = `<div class="list-group-item list-group-item-light">${header}</div>`;
            groups.forEach(g => {
                const btn = document.createElement('button');
                btn.type = 'button';
                btn.className = 'list-group-item list-group-item-action';
                btn.textContent = g.name;
                btn.dataset.groupId = g.id;
                btn.addEventListener('click', () => {
                    groupInput.value = g.name;
                    currentGroupIdField.value = g.id;
                    if (groupIdHiddenField) groupIdHiddenField.value = g.id;
                    groupSuggestions.style.display = 'none';
                    // Enable student input, reset selection; keep books disabled until student chosen
                    if (studentInput) { studentInput.disabled = false; studentInput.value = ''; studentInput.placeholder = 'Например: Иванов Иван'; studentIdField.value = ''; }
                    const bs = document.getElementById('bookSearch');
                    if (bs) { bs.disabled = true; bs.value = ''; bs.placeholder = 'Сначала выберите ФИО'; document.getElementById('book_id').value = ''; }
                    loadBooks(g.id);
                });
                groupSuggestions.appendChild(btn);
            });
        }
        groupSuggestions.style.display = 'block';
    }

    if (groupInput) {
        groupInput.addEventListener('input', function() {
            const q = this.value.trim();
            let results;
            if (!q) {
                // clear selected group when input is emptied
                currentGroupIdField.value = '';
                if (groupIdHiddenField) groupIdHiddenField.value = '';
                if (studentInput) { studentInput.disabled = true; studentInput.value = ''; studentIdField.value = ''; studentInput.placeholder = 'Сначала выберите группу'; }
                const bs = document.getElementById('bookSearch');
                if (bs) { bs.disabled = true; bs.value = ''; bs.placeholder = 'Сначала выберите группу'; document.getElementById('book_id').value = ''; }
                results = groupsList;
            } else {
                const qLower = q.toLowerCase();
                if (/^\d+$/.test(q)) {
                    // query is only digits -> match when any numeric part of group starts with the query
                    results = groupsList.filter(g => {
                        const nums = (g.name.match(/\d+/g) || []).map(n => n);
                        return nums.some(n => n.startsWith(q));
                    });
                } else if (/^\d/.test(q)) {
                    // starts with a digit but contains letters -> fallback to substring match
                    results = groupsList.filter(g => g.name.toLowerCase().includes(qLower));
                } else {
                    // otherwise require startsWith (first letter mandatory) and case-insensitive
                    results = groupsList.filter(g => g.name.toLowerCase().startsWith(qLower));
                }
            }
            renderGroupSuggestions(results, q ? `Результаты "${q}":` : 'Все группы:');
        });

        groupInput.addEventListener('click', function() {
            // Показываем все группы при клике
            renderGroupSuggestions(groupsList, 'Все группы:');
        });

        // Скрываем при клике вне
        document.addEventListener('click', e => {
            if (!groupInput.contains(e.target) && (!groupSuggestions || !groupSuggestions.contains(e.target))) {
                if (groupSuggestions) groupSuggestions.style.display = 'none';
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
            const bs = document.getElementById('bookSearch');

            if (!groupId) {
                showMessage('Сначала выберите группу');
                return;
            }

            // If student field cleared, clear selection and disable book input
            if (query === '') {
                studentIdField.value = '';
                if (bs) { bs.disabled = true; bs.value = ''; bs.placeholder = 'Сначала выберите ФИО'; document.getElementById('book_id').value = ''; }
                loadAllStudents(groupId);
                return;
            }

            // While typing (not yet selected), books remain disabled
            if (bs) { bs.disabled = true; bs.placeholder = 'Сначала выберите ФИО'; }

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
                    // Enable book search now that a student is chosen
                    const bs = document.getElementById('bookSearch');
                    if (bs) {
                        bs.disabled = false;
                        bs.placeholder = 'Начните вводить название или автора...';
                    }
                    // If a book is already selected and we have available copies, enable quantity controls
                    const qty = document.getElementById('copyQuantity');
                    const qtyPlus = document.getElementById('qtyPlus');
                    const qtyMinus = document.getElementById('qtyMinus');
                    if (qty && availableCopies && availableCopies.length > 0) {
                        qty.disabled = false;
                        qtyPlus.disabled = false;
                        qtyMinus.disabled = false;
                        document.getElementById('qtyHint').textContent = `Доступно: ${availableCopies.length}. Выберите количество`;
                    }
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
                groupsList = groups || [];
                // сортируем по имени для удобства
                groupsList.sort((a,b) => a.name.localeCompare(b.name, 'ru'));
            })
            .catch(err => {
                console.error(err);
                groupsList = [];
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
        // update hidden fields and quantity input sync
        const copyHidden = document.getElementById('copy_codes_hidden');
        const qtyHidden = document.getElementById('quantity_hidden');
        if (copyHidden) copyHidden.value = codes.join(',');
        if (qtyHidden) qtyHidden.value = codes.length;
        const qi = document.getElementById('copyQuantity');
        if (qi) qi.value = codes.length;
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

    // флаг: если успех был из отправки запроса — после закрытия модалки перезагружаем страницу
    let successModalReloadOnClose = false;

    function showSuccessModal(message) {
        const match = message.match(/#(\d+)/);
        if (match) {
            const id = match[1];
            const el = document.getElementById('requestId');
            if (el) {
                el.textContent = id;
                el.dataset.fullNumber = id;
            }
            successModalReloadOnClose = true;
            const modalEl = document.getElementById('successModal');
            const modal = new bootstrap.Modal(modalEl);
            modal.show();
        } else {
            alert(message);
        }
    }

    // Если successModal закрылся — обновляем страницу (чтобы точно сбросить все поля)
    const successModalElement = document.getElementById('successModal');
    if (successModalElement) {
        successModalElement.addEventListener('hidden.bs.modal', function () {
            if (successModalReloadOnClose) {
                // Полная перезагрузка страницы
                window.location.reload();
            }
        });
    }

    document.getElementById('checkStatusBtn').addEventListener('click', function() {
        const el = document.getElementById('requestId');
        const id = el.dataset.fullNumber || '';
        // Если пользователь переходит на страницу статуса — не нужно перезагружать страницу после скрытия модалки
        successModalReloadOnClose = false;
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
        // update hidden fields and quantity input sync
        const copyHidden = document.getElementById('copy_codes_hidden');
        const qtyHidden = document.getElementById('quantity_hidden');
        if (copyHidden) copyHidden.value = codes.join(',');
        if (qtyHidden) qtyHidden.value = codes.length;
        const qi = document.getElementById('copyQuantity');
        if (qi) qi.value = codes.length;
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
                    item.onclick = async () => {
                        bookSearchInput.value = b.name;
                        bookIdField.value = b.id;
                        bookSuggestions.style.display = 'none';

                        // Fetch available copies for this book (sorted by numeric instance)
                        try {
                            const res = await fetch(`/get-available-copies/${b.id}`);
                            if (res.ok) {
                                availableCopies = await res.json();
                            } else {
                                availableCopies = [];
                            }
                        } catch (err) {
                            console.error('Ошибка получения копий', err);
                            availableCopies = [];
                        }

                        // Setup quantity control based on availability; only enable if student selected
                        const qty = document.getElementById('copyQuantity');
                        const qtyPlus = document.getElementById('qtyPlus');
                        const qtyMinus = document.getElementById('qtyMinus');
                        if (availableCopies.length === 0) {
                            if (qty) { qty.value = 0; qty.min = 0; qty.max = 0; qty.disabled = true; }
                            if (qtyPlus) qtyPlus.disabled = true;
                            if (qtyMinus) qtyMinus.disabled = true;
                            document.getElementById('qtyHint').textContent = 'Нет доступных экземпляров для выбранной книги';
                            showMessage('Нет доступных экземпляров для выбранной книги');
                        } else {
                            if (qty) { qty.min = 0; qty.max = availableCopies.length; qty.value = 0; }
                            if (studentIdField.value) {
                                if (qty) qty.disabled = false;
                                if (qtyPlus) qtyPlus.disabled = false;
                                if (qtyMinus) qtyMinus.disabled = false;
                                document.getElementById('qtyHint').textContent = `Доступно: ${availableCopies.length}. Выберите количество`;
                            } else {
                                if (qty) qty.disabled = true;
                                if (qtyPlus) qtyPlus.disabled = true;
                                if (qtyMinus) qtyMinus.disabled = true;
                                document.getElementById('qtyHint').textContent = `Доступно: ${availableCopies.length}. Сначала выберите ФИО`;
                            }
                        }

                        // Clear auto-assigned codes when selecting another book
                        studentScannedCodes.clear();
                        updateStudentAttached();
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

        // Quantity controls
        const qtyInput = document.getElementById('copyQuantity');
        const qtyPlusBtn = document.getElementById('qtyPlus');
        const qtyMinusBtn = document.getElementById('qtyMinus');

        function assignCopiesByQuantity(n) {
            // n is desired number; choose first n available copies in numeric order
            if (!availableCopies || availableCopies.length === 0 || n <= 0) {
                studentScannedCodes = new Set();
                updateStudentAttached();
                return;
            }
            if (n > availableCopies.length) n = availableCopies.length;
            const selected = availableCopies.slice(0, n);
            studentScannedCodes = new Set(selected);
            updateStudentAttached();
        }

        if (qtyPlusBtn && qtyMinusBtn && qtyInput) {
            qtyPlusBtn.addEventListener('click', () => {
                let val = parseInt(qtyInput.value || '0', 10);
                const max = parseInt(qtyInput.max || '0', 10);
                if (val < max) {
                    val++;
                    qtyInput.value = val;
                    assignCopiesByQuantity(val);
                }
            });

            qtyMinusBtn.addEventListener('click', () => {
                let val = parseInt(qtyInput.value || '0', 10);
                if (val > 0) {
                    val--;
                    qtyInput.value = val;
                    assignCopiesByQuantity(val);
                }
            });

            qtyInput.addEventListener('input', () => {
                let val = parseInt(qtyInput.value || '0', 10);
                if (isNaN(val) || val < 0) val = 0;
                const max = parseInt(qtyInput.max || '0', 10);
                if (val > max) val = max;
                qtyInput.value = val;
                assignCopiesByQuantity(val);
            });
        }
    }
});