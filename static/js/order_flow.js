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
                const pdf = await window.pdfjsLib.getDocument({ data: fileArrayBuffer }).promise;
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
            docPagesSpan.textContent = 'Detected';
        }

        fetchQuote();
    }

    // Range select toggles
    pageRangeSelect.addEventListener('change', () => {
        if (pageRangeSelect.value === 'CUSTOM') {
            customRangeDiv.classList.remove('d-none');
        } else {
            customRangeDiv.classList.add('d-none');
        }
        fetchQuote();
    });

    // Event listeners for recalculating price quote
    [...colorModeRadios, ...duplexRadios, ...paperSizeRadios].forEach(el => el.addEventListener('change', fetchQuote));
    copiesInput.addEventListener('input', fetchQuote);
    customRangeInput.addEventListener('input', fetchQuote);

    function getSelectedRadio(radios) {
        for (const r of radios) {
            if (r.checked) return r.value;
        }
        return '';
    }

    async function fetchQuote() {
        if (!selectedFile) return;

        const payload = {
            shop_slug: shopSlug,
            page_count: detectedPages,
            color_mode: getSelectedRadio(colorModeRadios) || 'BW',
            duplex_mode: getSelectedRadio(duplexRadios) || 'SINGLE',
            paper_size: getSelectedRadio(paperSizeRadios) || 'A4',
            copies: parseInt(copiesInput.value) || 1,
            page_range_type: pageRangeSelect.value,
            page_range_selection: customRangeInput.value.trim()
        };

        try {
            const resp = await fetch('/orders/api/quote/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (resp.ok) {
                const data = await resp.json();
                quoteTotalSpan.textContent = `₹ ${data.total_amount.toFixed(2)}`;
                quoteBreakdownDiv.innerHTML = `
                    <div class="small text-muted mb-1">Rate: ₹${data.unit_rate} (${data.rate_label})</div>
                    <div class="small text-muted mb-1">Total physical sheets: ${data.total_sheets} (${data.copies} copies)</div>
                `;
                submitOrderBtn.disabled = false;
            }
        } catch (err) {
            console.error('Error fetching quote:', err);
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
            // 1. Client-Side Encryption
            const cryptoRes = await ClientCryptoManager.encryptDocument(fileArrayBuffer, rsaPublicKey);

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

            const uploadResp = await fetch('/orders/api/upload/', {
                method: 'POST',
                body: formData
            });

            if (!uploadResp.ok) {
                const errData = await uploadResp.json();
                throw new Error(errData.error || 'Document upload failed.');
            }

            const docData = await uploadResp.json();
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
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(orderPayload)
            });

            if (!orderResp.ok) {
                const errData = await orderResp.json();
                throw new Error(errData.error || 'Failed to create order.');
            }

            const orderData = await orderResp.json();
            const orderNumber = orderData.order_number;

            uploadStatusAlert.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Initiating secure payment gateway...';

            // 4. Initiate Payment
            const payResp = await fetch('/payments/api/create-order/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ order_number: orderNumber })
            });

            if (!payResp.ok) {
                const errData = await payResp.json();
                throw new Error(errData.error || 'Failed to initiate payment.');
            }

            const payData = await payResp.json();

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
                        name: customerName,
                        contact: customerPhone
                    },
                    theme: { color: '#0F172A' }
                };
                const rzp = new window.Razorpay(rzpOptions);
                rzp.open();
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
        const verifyResp = await fetch('/payments/api/verify/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                gateway_order_id: orderId,
                gateway_payment_id: paymentId,
                gateway_signature: signature
            })
        });

        if (verifyResp.ok) {
            const res = await verifyResp.json();
            window.location.href = res.redirect_url || `/orders/track/${orderNumber}/`;
        } else {
            const errData = await verifyResp.json();
            alert('Payment verification failed: ' + (errData.error || 'Signature error'));
            submitOrderBtn.disabled = false;
        }
    }
});
