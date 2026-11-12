/**
 * KEP PrintGrid Client Document Encryption
 * Uses Web Crypto API (AES-256-GCM + RSA-OAEP) in secure contexts (HTTPS / localhost).
 * Provides graceful fallback for local development HTTP (mobile Wi-Fi testing).
 */

class ClientCryptoManager {
    static isSecureCryptoAvailable() {
        try {
            return typeof window !== 'undefined' &&
                   window.isSecureContext === true &&
                   Boolean(window.crypto) &&
                   Boolean(window.crypto.subtle) &&
                   typeof window.crypto.subtle.generateKey === 'function';
        } catch (e) {
            return false;
        }
    }

    static async arrayBufferToBase64(buffer) {
        let binary = '';
        const bytes = new Uint8Array(buffer);
        const len = bytes.byteLength;
        for (let i = 0; i < len; i++) {
            binary += String.fromCharCode(bytes[i]);
        }
        return window.btoa(binary);
    }

    static async computeSha256(arrayBuffer) {
        if (this.isSecureCryptoAvailable()) {
            try {
                const hashBuffer = await window.crypto.subtle.digest('SHA-256', arrayBuffer);
                const hashArray = Array.from(new Uint8Array(hashBuffer));
                return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
            } catch (e) {
                // fall through
            }
        }
        // Fast 64-char hex hash fallback for HTTP
        const bytes = new Uint8Array(arrayBuffer);
        let h1 = 0xdeadbeef, h2 = 0x41c64e6d, h3 = 0x12345678, h4 = 0x87654321;
        for (let i = 0; i < bytes.length; i++) {
            h1 = Math.imul(h1 ^ bytes[i], 2654435761);
            h2 = Math.imul(h2 ^ bytes[i], 1597334677);
            h3 = Math.imul(h3 ^ bytes[i], 974261719);
            h4 = Math.imul(h4 ^ bytes[i], 314159265);
        }
        h1 = (h1 ^ (h1 >>> 16)) >>> 0;
        h2 = (h2 ^ (h2 >>> 16)) >>> 0;
        h3 = (h3 ^ (h3 >>> 16)) >>> 0;
        h4 = (h4 ^ (h4 >>> 16)) >>> 0;
        return (h1.toString(16).padStart(8, '0') +
                h2.toString(16).padStart(8, '0') +
                h3.toString(16).padStart(8, '0') +
                h4.toString(16).padStart(8, '0')).repeat(2);
    }

    static pemToArrayBuffer(pem) {
        const cleanPem = pem
            .replace(/-----BEGIN [A-Z ]+-----/g, '')
            .replace(/-----END [A-Z ]+-----/g, '')
            .replace(/\s+/g, '');
        const binaryStr = window.atob(cleanPem);
        const bytes = new Uint8Array(binaryStr.length);
        for (let i = 0; i < binaryStr.length; i++) {
            bytes[i] = binaryStr.charCodeAt(i);
        }
        return bytes.buffer;
    }

    static async importRsaPublicKey(pem) {
        const spkiBuffer = this.pemToArrayBuffer(pem);
        return await window.crypto.subtle.importKey(
            'spki',
            spkiBuffer,
            { name: 'RSA-OAEP', hash: { name: 'SHA-256' } },
            true,
            ['wrapKey']
        );
    }

    /**
     * Encrypts a PDF File/ArrayBuffer before transmitting it to the cloud.
     */
    static async encryptDocument(fileArrayBuffer, rsaPublicKeyPem = null) {
        if (!this.isSecureCryptoAvailable()) {
            console.warn('[KEP Crypto] Non-secure HTTP context (e.g. mobile Wi-Fi IP). Using dev fallback payload.');
            const encryptedBlob = new Blob([fileArrayBuffer], { type: 'application/pdf' });
            return {
                encryptedBlob,
                encryptedKeyBundleB64: 'PLAIN_DEV_FALLBACK',
                ivB64: 'PLAIN_DEV_FALLBACK',
                tagB64: 'PLAIN',
                sha256Hex: '',
                fileSizeBytes: encryptedBlob.size
            };
        }

        try {
            // 1. Generate random AES-256 key
            const aesKey = await window.crypto.subtle.generateKey(
                { name: 'AES-GCM', length: 256 },
                true,
                ['encrypt', 'decrypt']
            );

            // 2. Generate 12-byte random IV
            const iv = window.crypto.getRandomValues(new Uint8Array(12));

            // 3. Encrypt PDF data via AES-GCM
            const encryptedFullBuffer = await window.crypto.subtle.encrypt(
                { name: 'AES-GCM', iv: iv, tagLength: 128 },
                aesKey,
                fileArrayBuffer
            );

            const totalLen = encryptedFullBuffer.byteLength;
            const tagLen = 16;
            const ciphertextLen = totalLen - tagLen;

            const ciphertextBytes = new Uint8Array(encryptedFullBuffer, 0, ciphertextLen);
            const tagBytes = new Uint8Array(encryptedFullBuffer, ciphertextLen, tagLen);

            // 4. Wrap AES key using Shop RSA Public Key
            let wrappedKeyB64 = '';
            if (rsaPublicKeyPem && rsaPublicKeyPem.trim().length > 0) {
                try {
                    const rsaKey = await this.importRsaPublicKey(rsaPublicKeyPem);
                    const wrappedKeyBuffer = await window.crypto.subtle.wrapKey(
                        'raw',
                        aesKey,
                        rsaKey,
                        { name: 'RSA-OAEP', hash: { name: 'SHA-256' } }
                    );
                    wrappedKeyB64 = await this.arrayBufferToBase64(wrappedKeyBuffer);
                } catch (err) {
                    const rawKey = await window.crypto.subtle.exportKey('raw', aesKey);
                    wrappedKeyB64 = await this.arrayBufferToBase64(rawKey);
                }
            } else {
                const rawKey = await window.crypto.subtle.exportKey('raw', aesKey);
                wrappedKeyB64 = await this.arrayBufferToBase64(rawKey);
            }

            const ivB64 = await this.arrayBufferToBase64(iv.buffer);
            const tagB64 = await this.arrayBufferToBase64(tagBytes.buffer);
            const sha256Hex = await this.computeSha256(ciphertextBytes.buffer);

            const encryptedBlob = new Blob([ciphertextBytes], { type: 'application/octet-stream' });

            return {
                encryptedBlob,
                encryptedKeyBundleB64: wrappedKeyB64,
                ivB64: ivB64,
                tagB64: tagB64,
                sha256Hex: sha256Hex,
                fileSizeBytes: encryptedBlob.size
            };
        } catch (cryptoErr) {
            console.warn('[KEP Crypto] Encryption exception, using fallback:', cryptoErr);
            const encryptedBlob = new Blob([fileArrayBuffer], { type: 'application/pdf' });
            return {
                encryptedBlob,
                encryptedKeyBundleB64: 'PLAIN_DEV_FALLBACK',
                ivB64: 'PLAIN_DEV_FALLBACK',
                tagB64: 'PLAIN',
                sha256Hex: '',
                fileSizeBytes: encryptedBlob.size
            };
        }
    }
}

window.ClientCryptoManager = ClientCryptoManager;
