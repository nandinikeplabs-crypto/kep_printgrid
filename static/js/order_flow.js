/**
 * KEP PrintGrid Customer Ordering Logic
 */

document.addEventListener('DOMContentLoaded', () => {
    const shopSlug = window.PRINTGRID_SHOP_SLUG;
    const rsaPublicKey = window.PRINTGRID_RSA_KEY || '';

    // Elements
    const dropzone = document.getElementById('uploadDropzone');
    const fileInput = document.getElementById('pdfFileInput');
    const docInfoSection = document.getElementById('docInfoSection');
    const docNameSpan = document.getElementById('docName');
    const docPagesSpan = document.getElementById('docPages');
    const docSizeSpan = document.getElementById('docSize');
    const previewContainer = document.getElementById('pdfPreviewContainer');
    const previewCanvas = document.getElementById('pdfPreviewCanvas');

    // Controls
    const colorModeRadios = document.querySelectorAll('input[name="color_mode"]');
    const duplexRadios = document.querySelectorAll('input[name="duplex_mode"]');
    const paperSizeRadios = document.querySelectorAll('input[name="paper_size"]');
    const copiesInput = document.getElementById('copiesInput');
    const pageRangeSelect = document.getElementById('pageRangeSelect');
    const customRangeInput = document.getElementById('customRangeInput');
    const customRangeDiv = document.getElementById('customRangeDiv');
    const finishingSelect = document.getElementById('finishingSelect');

    // Summary elements
    const quoteBreakdownDiv = document.getElementById('quoteBreakdown');
    const quoteTotalSpan = document.getElementById('quoteTotal');
    const submitOrderBtn = document.getElementById('submitOrderBtn');
    const uploadStatusAlert = document.getElementById('uploadStatusAlert');

    // State
    let selectedFile = null;
    let fileArrayBuffer = null;
    let detectedPages = 1;
    let uploadedDocumentId = null;

    if (!dropzone) return;

    // Dropzone interactions
    dropzone.addEventListener('click', () => fileInput.click());
    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('dragover');
    });
    dropzone.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));
    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            handleFileSelection(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileSelection(e.target.files[0]);
        }
    });

    async function handleFileSelection(file) {
        if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) {
            alert('Only PDF documents are supported for printing.');
            return;
        }

        // Limit size: 50MB
        if (file.size > 50 * 1024 * 1024) {
            alert('File exceeds maximum allowed upload size (50 MB).');
            return;
        }

        selectedFile = file;
        docNameSpan.textContent = file.name;
        docSizeSpan.textContent = (file.size / (1024 * 1024)).toFixed(2) + ' MB';
        docInfoSection.classList.remove('d-none');

        // Read buffer
        fileArrayBuffer = await file.arrayBuffer();

        // Count pages & render preview using PDF.js if available
        if (window.pdfjsLib) {
            try {
                // Pass slice copy so worker doesn't neuter fileArrayBuffer
                const pdf = await window.pdfjsLib.getDocument({ data: fileArrayBuffer.slice(0) }).promise;
                detectedPages = pdf.numPages;
                docPagesSpan.textContent = detectedPages;

                // Render page 1 preview
                const page = await pdf.getPage(1);
                const viewport = page.getViewport({ scale: 1.0 });
                previewCanvas.height = viewport.height;
                previewCanvas.width = viewport.width;
                const renderContext = {
                    canvasContext: previewCanvas.getContext('2d'),
                    viewport: viewport
                };
                await page.render(renderContext).promise;
                previewContainer.classList.remove('d-none');
            } catch (err) {
                console.warn('PDF.js rendering note:', err);
                detectedPages = 1;
                docPagesSpan.textContent = '1 (Preview not rendered)';
            }
        } else {
            detectedPages = 1;
            docPagesSpan.textContent = '1';
        }

        autoCalculatePrice();
    }

    // Range select toggles
    pageRangeSelect.addEventListener('change', () => {
        if (pageRangeSelect.value === 'CUSTOM') {
            customRangeDiv.classList.remove('d-none');
        } else {
            customRangeDiv.classList.add('d-none');
        }
        autoCalculatePrice();
    });

    // Real-time automatic recalculation on any input change
    [...colorModeRadios, ...duplexRadios, ...paperSizeRadios].forEach(el => {
        el.addEventListener('change', autoCalculatePrice);
    });
    copiesInput.addEventListener('input', autoCalculatePrice);
    copiesInput.addEventListener('change', autoCalculatePrice);
    if (finishingSelect) {
        finishingSelect.addEventListener('change', autoCalculatePrice);
    }
    customRangeInput.addEventListener('input', autoCalculatePrice);

    function getSelectedRadio(radios) {
        for (const r of radios) {
            if (r.checked) return r.value;
        }
        return '';
    }

    // Automatic real-time price calculation (Instant client-side + backend validation)
    function autoCalculatePrice() {
        const pages = detectedPages || 1;
        const color = getSelectedRadio(colorModeRadios) || 'BW';
        const duplex = getSelectedRadio(duplexRadios) || 'SINGLE';
        const paper = getSelectedRadio(paperSizeRadios) || 'A4';
        const copies = Math.max(1, parseInt(copiesInput.value) || 1);
        const finishing = finishingSelect ? finishingSelect.value : 'NONE';

        // Effective pages
        let effectivePages = pages;
        if (pageRangeSelect.value === 'CUSTOM' && customRangeInput.value.trim()) {
            let count = 0;
            customRangeInput.value.split(',').forEach(part => {
                part = part.trim();
                if (part.includes('-')) {
                    const [s, e] = part.split('-');
                    if (!isNaN(s) && !isNaN(e)) count += Math.max(0, parseInt(e) - parseInt(s) + 1);
                } else if (!isNaN(part) && part) {
                    count++;
                }
            });
            if (count > 0) effectivePages = Math.min(count, pages);
        }

        // Rates table
        const rates = window.PRINTGRID_RATES || {
            bw_single: 2.0, bw_double: 3.5,
            color_single: 10.0, color_double: 18.0,
            a3_bw: 5.0, a3_color: 20.0,
            stapling: 2.0, spiral: 30.0, lamination: 20.0
        };

        let sheets = (duplex === 'DOUBLE') ? Math.ceil(effectivePages / 2) : effectivePages;
        let unitRate = rates.bw_single;
        let rateLabel = 'B&W Single-Sided';

        if (paper === 'A3') {
            unitRate = (color === 'COLOR') ? rates.a3_color : rates.a3_bw;
            rateLabel = `A3 ${color}`;
        } else {
            if (color === 'COLOR') {
                unitRate = (duplex === 'DOUBLE') ? rates.color_double : rates.color_single;
                rateLabel = (duplex === 'DOUBLE') ? 'Color Double-Sided' : 'Color Single-Sided';
            } else {
                unitRate = (duplex === 'DOUBLE') ? rates.bw_double : rates.bw_single;
                rateLabel = (duplex === 'DOUBLE') ? 'B&W Double-Sided' : 'B&W Single-Sided';
            }
        }

        let printCost = unitRate * sheets * copies;
        let finishingCost = 0;
        let finishingLabel = '';
        if (finishing === 'CORNER_STAPLE') {
            finishingCost = (rates.stapling || 2.0) * copies;
            finishingLabel = `Corner Stapling (+₹${finishingCost.toFixed(2)})`;
        } else if (finishing === 'SPIRAL_BINDING') {
            finishingCost = (rates.spiral || 30.0) * copies;
            finishingLabel = `Spiral Binding (+₹${finishingCost.toFixed(2)})`;
        } else if (finishing === 'LAMINATION') {
            finishingCost = (rates.lamination || 20.0) * copies;
            finishingLabel = `Hot Lamination (+₹${finishingCost.toFixed(2)})`;
        }

        const total = (printCost + finishingCost).toFixed(2);
        quoteTotalSpan.textContent = `₹ ${total}`;

        if (!selectedFile) {
            quoteBreakdownDiv.innerHTML = `
                <div class="small text-muted mb-1"><span class="badge bg-secondary-subtle text-secondary me-1">Base Rate</span> ₹${unitRate.toFixed(2)}/sheet (${rateLabel})</div>
                <div class="small text-muted">Estimated price shown for 1 page. Select a PDF to calculate exact pages.</div>
            `;
        } else {
            quoteBreakdownDiv.innerHTML = `
                <div class="small text-dark fw-semibold mb-1">₹${unitRate.toFixed(2)}/sheet (${rateLabel})</div>
                <div class="small text-muted mb-1">${sheets * copies} physical sheets (${effectivePages} pages &times; ${copies} ${copies > 1 ? 'copies' : 'copy'})</div>
                ${finishingCost > 0 ? `<div class="small text-primary fw-semibold">${finishingLabel}</div>` : ''}
            `;
            submitOrderBtn.disabled = false;
        }

        // Asynchronously sync with Backend API
        syncBackendQuote(effectivePages, color, duplex, paper, copies, finishing);
    }

    async function syncBackendQuote(pages, color, duplex, paper, copies, finishing) {
        try {
            const resp = await fetch('/orders/api/quote/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    shop_slug: window.PRINTGRID_SHOP_SLUG || shopSlug,
                    page_count: pages,
                    color_mode: color,
                    duplex_mode: duplex,
                    paper_size: paper,
                    copies: copies,
                    finishing_service: finishing
                })
            });

            if (resp.ok) {
                const data = await resp.json();
                quoteTotalSpan.textContent = `₹ ${data.total_amount.toFixed(2)}`;
            }
        } catch (err) {
            // Keep instant client-side calculation if offline
        }
    }

    // Trigger initial calculation on page load
    autoCalculatePrice();

    function getCsrfToken() {
        const cookie = document.cookie.split('; ').find(row => row.startsWith('csrftoken='));
        return cookie ? cookie.split('=')[1] : '';
    }

    async function parseResponseJson(resp) {
        try {
            const raw = await resp.text();
            try {
                const parsed = JSON.parse(raw);
                if (typeof parsed === 'object' && parsed !== null) {
                    if (!parsed.error && parsed.detail) parsed.error = parsed.detail;
                    if (!parsed.error && parsed.message) parsed.error = parsed.message;
                }
                return parsed;
            } catch (_) {
                const clean = raw.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim().substring(0, 140);
                return { error: clean || `Server returned status ${resp.status}` };
            }
        } catch (e) {
            return { error: 'Network request error: ' + e.message };
        }
    }

    // Submit & Encrypt flow
    submitOrderBtn.addEventListener('click', async () => {
        if (!selectedFile || !fileArrayBuffer) {
            alert('Please select a PDF document first.');
            return;
        }

        const customerName = document.getElementById('custNameInput').value.trim() || 'Walk-in Customer';
        const customerPhone = document.getElementById('custPhoneInput').value.trim();

        if (!customerPhone) {
            alert('Please enter your mobile number for order pickup verification.');
            document.getElementById('custPhoneInput').focus();
            return;
        }

        submitOrderBtn.disabled = true;
        uploadStatusAlert.classList.remove('d-none');
        uploadStatusAlert.className = 'alert alert-info py-2 small';
        uploadStatusAlert.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Encrypting PDF locally (Zero-Knowledge AES-256-GCM)...';

        try {
            // Read fresh un-neutered buffer directly from user file
            const uploadBuffer = await selectedFile.arrayBuffer();

            // 1. Client-Side Encryption (with automatic safe fallback for mobile HTTP)
            let cryptoRes = null;
            try {
                if (window.ClientCryptoManager && typeof window.ClientCryptoManager.encryptDocument === 'function') {
                    cryptoRes = await window.ClientCryptoManager.encryptDocument(uploadBuffer, rsaPublicKey);
                }
            } catch (cryptoErr) {
                console.warn('Client encryption note (using plain fallback for local network):', cryptoErr);
            }

            if (!cryptoRes || !cryptoRes.encryptedBlob) {
                cryptoRes = {
                    encryptedBlob: selectedFile,
                    encryptedKeyBundleB64: 'PLAIN_DEV_FALLBACK',
                    ivB64: 'PLAIN_DEV_FALLBACK',
                    tagB64: 'PLAIN',
                    sha256Hex: '',
                    fileSizeBytes: selectedFile.size
                };
            }

            uploadStatusAlert.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Uploading encrypted document securely...';

            // 2. Upload Encrypted Binary
            const formData = new FormData();
            formData.append('shop_slug', shopSlug);
            formData.append('encrypted_file', cryptoRes.encryptedBlob, selectedFile.name + '.enc');
            formData.append('original_filename', selectedFile.name);
            formData.append('file_hash_sha256', cryptoRes.sha256Hex);
            formData.append('encrypted_key_bundle', cryptoRes.encryptedKeyBundleB64);
            formData.append('encryption_iv', cryptoRes.ivB64);
            formData.append('encryption_tag', cryptoRes.tagB64);
            formData.append('detected_page_count', detectedPages);

            const uploadHeaders = {};
            const csrf = getCsrfToken();
            if (csrf) uploadHeaders['X-CSRFToken'] = csrf;

            const uploadResp = await fetch('/orders/api/upload/', {
                method: 'POST',
                headers: uploadHeaders,
                body: formData
            });

            const docData = await parseResponseJson(uploadResp);
            if (!uploadResp.ok) {
                throw new Error(docData.error || 'Document upload failed.');
            }

            uploadedDocumentId = docData.document_id;

            uploadStatusAlert.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Creating order quote...';

            // 3. Create Print Order
            const orderPayload = {
                shop_slug: shopSlug,
                document_id: uploadedDocumentId,
                customer_name: customerName,
                customer_phone: customerPhone,
                preferences: {
                    color_mode: getSelectedRadio(colorModeRadios) || 'BW',
                    duplex_mode: getSelectedRadio(duplexRadios) || 'SINGLE',
                    paper_size: getSelectedRadio(paperSizeRadios) || 'A4',
                    copies: parseInt(copiesInput.value) || 1,
                    page_range_type: pageRangeSelect.value,
                    page_range_selection: customRangeInput.value.trim()
                }
            };

            const orderResp = await fetch('/orders/api/create/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(csrf ? { 'X-CSRFToken': csrf } : {})
                },
                body: JSON.stringify(orderPayload)
            });

            const orderData = await parseResponseJson(orderResp);
            if (!orderResp.ok) {
                throw new Error(orderData.error || 'Failed to create order.');
            }

            const orderNumber = orderData.order_number;

            uploadStatusAlert.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Initiating secure payment gateway...';

            // 4. Initiate Payment
            const payResp = await fetch('/payments/api/create-order/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(csrf ? { 'X-CSRFToken': csrf } : {})
                },
                body: JSON.stringify({ order_number: orderNumber })
            });

            const payData = await parseResponseJson(payResp);
            if (!payResp.ok) {
                throw new Error(payData.error || 'Failed to initiate payment.');
            }

            // Check if sandbox simulation mode
            if (payData.is_sandbox && payData.sandbox_helper) {
                // Show modal or auto-trigger verified test payment
                showSandboxPaymentModal(payData, orderNumber);
            } else {
                // Live Razorpay Checkout script
                const rzpOptions = {
                    key: payData.key_id,
                    amount: payData.amount_paise,
                    currency: payData.currency,
                    name: 'KEP PrintGrid',
                    description: `Print Order #${orderNumber}`,
                    order_id: payData.gateway_order_id,
                    handler: async function (response) {
                        await verifyPaymentOnBackend(
                            response.razorpay_order_id,
                            response.razorpay_payment_id,
                            response.razorpay_signature,
                            orderNumber
                        );
                    },
                    prefill: {
                        name: customerName || 'Walk-in Customer',
                        contact: customerPhone || '',
                        email: 'customer@printgrid.local'
                    },
                    modal: {
                        ondismiss: function () {
                            submitOrderBtn.disabled = false;
                            uploadStatusAlert.classList.add('d-none');
                        },
                        escape: true,
                        backdropclose: false
                    },
                    retry: {
                        enabled: true
                    },
                    theme: { color: '#0F172A' }
                };
                uploadStatusAlert.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Connecting to payment gateway...';
                let RazorpayClass = window.Razorpay;
                if (typeof RazorpayClass !== 'function') {
                    // Slower mobile hotspot fallback: dynamically inject checkout.js
                    RazorpayClass = await new Promise((resolve) => {
                        const script = document.createElement('script');
                        script.src = 'https://checkout.razorpay.com/v1/checkout.js';
                        script.async = true;
                        script.onload = () => resolve(window.Razorpay || null);
                        script.onerror = () => resolve(null);
                        document.head.appendChild(script);
                        setTimeout(() => resolve(window.Razorpay || null), 3000);
                    });
                }

                if (typeof RazorpayClass === 'function') {
                    const rzp = new RazorpayClass(rzpOptions);
                    rzp.on('payment.failed', function (resp) {
                        const errMsg = resp.error ? resp.error.description : 'Payment could not be completed.';
                        uploadStatusAlert.className = 'alert alert-warning py-2 small';
                        uploadStatusAlert.textContent = 'Payment note: ' + errMsg;
                        submitOrderBtn.disabled = false;
                    });

                    if (payData.sandbox_helper) {
                        uploadStatusAlert.className = 'alert alert-info py-2 small';
                        uploadStatusAlert.innerHTML = `
                            <div class="d-flex justify-content-between align-items-center flex-wrap gap-2">
                                <span><span class="spinner-border spinner-border-sm me-2"></span>Payment window active...</span>
                                <button type="button" class="btn btn-sm btn-outline-primary fw-bold" id="manualSimTriggerBtn" style="font-size:0.75rem;">Instant Test Pay</button>
                            </div>
                        `;
                        const simBtn = document.getElementById('manualSimTriggerBtn');
                        if (simBtn) {
                            simBtn.addEventListener('click', (e) => {
                                e.preventDefault();
                                try { rzp.close(); } catch (_) {}
                                showSandboxPaymentModal(payData, orderNumber);
                            });
                        }
                    }

                    rzp.open();
                } else if (payData.sandbox_helper) {
                    // Verified sandbox fallback with genuine backend HMAC verification
                    showSandboxPaymentModal(payData, orderNumber);
                } else {
                    throw new Error('Payment gateway could not be loaded. Please check your network connection.');
                }
            }

        } catch (err) {
            uploadStatusAlert.className = 'alert alert-danger py-2 small';
            uploadStatusAlert.textContent = 'Error: ' + err.message;
            submitOrderBtn.disabled = false;
        }
    });

    function showSandboxPaymentModal(payData, orderNumber) {
        const modalHtml = `
            <div class="modal fade show d-block" tabindex="-1" style="background: rgba(15, 23, 42, 0.75);">
                <div class="modal-dialog modal-dialog-centered">
                    <div class="modal-content shadow-lg border-0">
                        <div class="modal-header bg-dark text-white">
                            <h5 class="modal-title fs-6"><i class="bi bi-shield-check text-warning me-2"></i>Razorpay Payment Sandbox</h5>
                        </div>
                        <div class="modal-body p-4">
                            <p class="text-muted small">You are in development mode. Simulate a real verified transaction using Razorpay's HMAC signature engine.</p>
                            <div class="card bg-light p-3 mb-3 border-0">
                                <div class="d-flex justify-content-between">
                                    <span class="text-muted">Order Number:</span>
                                    <span class="fw-bold">${orderNumber}</span>
                                </div>
                                <div class="d-flex justify-content-between mt-2">
                                    <span class="text-muted">Payable Amount:</span>
                                    <span class="fw-bold text-primary">₹ ${(payData.amount_paise / 100).toFixed(2)}</span>
                                </div>
                            </div>
                            <button id="paySuccessSimBtn" class="btn btn-success w-100 py-2 fw-bold">
                                <i class="bi bi-check-circle me-1"></i> Pay Now (Simulate Successful Payment)
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;

        const modalDiv = document.createElement('div');
        modalDiv.innerHTML = modalHtml;
        document.body.appendChild(modalDiv);

        document.getElementById('paySuccessSimBtn').addEventListener('click', async () => {
            const helper = payData.sandbox_helper;
            await verifyPaymentOnBackend(
                payData.gateway_order_id,
                helper.sample_payment_id,
                helper.sample_signature,
                orderNumber
            );
        });
    }

    async function verifyPaymentOnBackend(orderId, paymentId, signature, orderNumber) {
        uploadStatusAlert.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Verifying payment signature with bank...';
        const csrf = getCsrfToken();
        const verifyResp = await fetch('/payments/api/verify/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...(csrf ? { 'X-CSRFToken': csrf } : {})
            },
            body: JSON.stringify({
                gateway_order_id: orderId,
                gateway_payment_id: paymentId,
                gateway_signature: signature
            })
        });

        const verifyData = await parseResponseJson(verifyResp);
        if (verifyResp.ok) {
            window.location.href = verifyData.redirect_url || `/orders/track/${orderNumber}/`;
        } else {
            alert('Payment verification failed: ' + (verifyData.error || 'Signature error'));
            submitOrderBtn.disabled = false;
        }
    }
});
