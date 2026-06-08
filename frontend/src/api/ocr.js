// ============================================================
//  独立 OCR 识别 API
// ============================================================
import request from './request'

/**
 * 上传文件进行 OCR 识别（不绑定项目）
 * @param {File} file - 文件对象
 * @returns {Promise} 识别结果
 */
export function recognizeFile(file) {
  const formData = new FormData()
  formData.append('file', file)
  return request.post('/ocr/recognize', formData, {
    timeout: 120000, // OCR 可能耗时较长，超时设为 120 秒
  })
}
