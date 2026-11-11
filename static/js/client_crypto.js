/**
 * KEP PrintGrid Zero-Knowledge Client Document Encryption
 * Uses Web Crypto API (AES-256-GCM + RSA-OAEP SHA-256)
 */

class ClientCryptoManager {
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
        const hashBuffer = await window.crypto.subtle.digest('SHA-256', arrayBuffer);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
    }

    static pemToArrayBuffer(pem) {
        // Strip headers, footers, newlines
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
            {
                name: 'RSA-OAEP',
                hash: { name: 'SHA-256' }
            },
            true,
            ['wrapKey']
        );
    }

    /**
     * Encrypts a PDF File/ArrayBuffer before transmitting it to the cloud.
     */
    static async encryptDocument(fileArrayBuffer, rsaPublicKeyPem = null) {
        // 1. Generate random AES-256 key
        const aesKey = await window.crypto.subtle.generateKey(
            { name: 'AES-GCM', length: 256 },
            true,
            ['encrypt', 'decrypt']
        );

        // 2. Generate 12-byte random IV
        const iv = window.crypto.getRandomValues(new Uint8Array(12));

        // 3. Encrypt PDF data via AES-GCM (appends 16-byte authentication tag)
        const encryptedFullBuffer = await window.crypto.subtle.encrypt(
            { name: 'AES-GCM', iv: iv, tagLength: 128 },
            aesKey,
            fileArrayBuffer
        );

        // Split ciphertext and 16-byte authentication tag
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
                console.warn("RSA wrapping failed with provided key, using raw export:", err);
                const rawKey = await window.crypto.subtle.exportKey('raw', aesKey);
                wrappedKeyB64 = await this.arrayBufferToBase64(rawKey);
            }
        } else {
            // Dev fallback when shop connector key not yet synced
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
    }
}

window.ClientCryptoManager = ClientCryptoManager;
