/**
 * File upload helper for presigned POST URLs.
 *
 * This module provides utilities for uploading files directly to storage
 * using presigned POST URLs returned by the API.
 */

export interface UploadInstruction {
  url: string;
  method: "POST";
  fields: Record<string, string>;
  objectKey: string;
  expiresAt: string;
  publicUrl?: string;
}

/**
 * Upload a file using a presigned POST instruction.
 *
 * @param instruction - Upload instruction from the API
 * @param file - File to upload
 * @param onProgress - Optional progress callback (0-100)
 * @returns Promise that resolves when upload completes
 * @throws Error if upload fails
 */
export async function uploadFile(
  instruction: UploadInstruction,
  file: File,
  onProgress?: (percent: number) => void,
): Promise<void> {
  // Build FormData with fields first, then file
  const formData = new FormData();

  // Fields must come before file in the form data
  Object.entries(instruction.fields).forEach(([key, value]) => {
    formData.append(key, value);
  });

  // Append the file (must be last)
  formData.append("file", file);

  // Use XMLHttpRequest for progress tracking
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();

    xhr.open("POST", instruction.url);

    // Track upload progress
    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable && onProgress) {
        const percent = Math.round((event.loaded / event.total) * 100);
        onProgress(percent);
      }
    };

    // Handle successful upload
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve();
      } else {
        reject(new Error(`Upload failed with status ${xhr.status}: ${xhr.statusText}`));
      }
    };

    // Handle network errors
    xhr.onerror = () => {
      reject(new Error("Network error during upload"));
    };

    // Handle abort
    xhr.onabort = () => {
      reject(new Error("Upload aborted"));
    };

    // Send the request
    xhr.send(formData);
  });
}
