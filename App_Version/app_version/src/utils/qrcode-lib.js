// QRCode 编码核心（基于 qrcode-npm / qrcode-generator 算法）
// 纯 JS 实现，无 DOM 依赖

// QR 编码模式常量（当前仅支持 8 位字节模式）
const QR_MODE = { MODE_8BIT_BYTE: 1 << 2 }
// QR 纠错等级：L(低), M(中), Q(较高), H(高)
const QR_ERROR = { L: 1, M: 0, Q: 3, H: 2 }

// 各版本（1-40）的对齐图案中心位置表，用于在矩阵中放置对齐图案
const PATTERN_POS_TABLE = [
  [], [6, 18], [6, 22], [6, 26], [6, 30], [6, 34], [6, 22, 38], [6, 24, 42], [6, 26, 46],
  [6, 28, 50], [6, 30, 54], [6, 32, 58], [6, 34, 62], [6, 26, 46, 66], [6, 26, 48, 70],
  [6, 26, 50, 74], [6, 30, 54, 78], [6, 30, 56, 82], [6, 30, 58, 86], [6, 34, 62, 90],
  [6, 28, 50, 72, 94], [6, 26, 50, 74, 98], [6, 30, 54, 78, 102], [6, 28, 54, 80, 106],
  [6, 32, 58, 84, 110], [6, 30, 58, 86, 114], [6, 34, 62, 90, 118], [6, 26, 50, 74, 98, 122],
  [6, 30, 54, 78, 102, 126], [6, 26, 52, 78, 104, 130], [6, 30, 56, 82, 108, 134],
  [6, 34, 60, 86, 112, 138], [6, 30, 58, 86, 114, 142], [6, 34, 62, 90, 118, 146],
  [6, 30, 54, 78, 102, 126, 150], [6, 24, 50, 76, 102, 128, 154],
  [6, 28, 54, 80, 106, 132, 158], [6, 32, 58, 84, 110, 136, 162],
  [6, 26, 52, 78, 104, 130, 156, 182], [6, 30, 56, 82, 108, 134, 160, 186],
  [6, 34, 62, 90, 118, 146, 174, 202]
]

// BCH 编码用生成多项式系数（G15 用于格式信息，G18 用于版本信息）
const G15 = 1335
const G18 = 7973
const G15_MASK = 0x5412

// 计算格式信息的 BCH 编码（含纠错码 + 掩码异或）
// 用于生成二维码矩阵中的格式信息区（纠错等级与掩码模式的编码）
function getBCHTypeInfo(d) {
  let d2 = d << 10
  while (getBCHDigit(d2) - getBCHDigit(G15) >= 0) {
    d2 ^= G15 << (getBCHDigit(d2) - getBCHDigit(G15))
  }
  return ((d << 10) | d2) ^ G15_MASK
}

// 计算版本信息的 BCH 编码（用于版本 7 及以上的二维码）
function getBCHTypeNumber(d) {
  let d2 = d << 12
  while (getBCHDigit(d2) - getBCHDigit(G18) >= 0) {
    d2 ^= G18 << (getBCHDigit(d2) - getBCHDigit(G18))
  }
  return (d << 12) | d2
}

// 计算整数二进制表示的位数（最高位 1 所在位置）
function getBCHDigit(d) {
  let digit = 0
  while (d !== 0) { digit++; d >>>= 1 }
  return digit
}

// 根据版本和纠错等级，获取 RS 纠错码块列表
// 每个块包含 [总字节数, 纠错码字节数]
function getRSECCBlocks(typeNumber, errorCorrectLevel) {
  const rsBlock = getRsBlockTable(typeNumber, errorCorrectLevel)
  if (!rsBlock) return []
  const list = []
  let totalCount = 0
  for (let i = 0; i < rsBlock.length; i += 3) {
    for (let j = 0; j < rsBlock[i]; j++) {
      list.push([rsBlock[i + 1], rsBlock[i + 2]])
      totalCount += rsBlock[i + 1]
    }
  }
  return list
}

// QR 码 RS 纠错块配置查找表（按版本 1-40 * 4 种纠错等级索引）
// 每组三个数字: [块数量, 每块总字节数, 每块数据字节数]
function getRsBlockTable(typeNumber, errorCorrectLevel) {
  const tbl = [
    [1, 26, 19], [1, 26, 16], [1, 26, 13], [1, 26, 9],
    [1, 44, 34], [1, 44, 28], [1, 44, 22], [1, 44, 16],
    [1, 70, 55], [1, 70, 44], [2, 35, 17], [2, 35, 13],
    [1, 100, 80], [2, 50, 32], [2, 50, 24], [4, 25, 9],
    [1, 134, 108], [2, 67, 43], [2, 33, 15, 2, 34, 16], [2, 33, 11, 2, 34, 12],
    [2, 86, 68], [4, 43, 27], [4, 43, 19], [4, 43, 15],
    [2, 98, 78], [4, 49, 31], [2, 32, 14, 4, 33, 15], [4, 39, 13, 1, 40, 14],
    [2, 121, 97], [2, 60, 38, 2, 61, 39], [4, 40, 18, 2, 41, 19], [4, 40, 14, 2, 41, 15],
    [2, 146, 116], [3, 58, 36, 2, 59, 37], [4, 36, 16, 4, 37, 17], [4, 36, 12, 4, 37, 13],
    [2, 86, 68, 2, 87, 69], [4, 69, 43, 1, 70, 44], [6, 43, 19, 2, 44, 20], [6, 43, 15, 2, 44, 16],
    [4, 101, 81], [1, 80, 50, 4, 81, 51], [4, 50, 22, 4, 51, 23], [3, 36, 12, 8, 37, 13],
    [2, 116, 92, 2, 117, 93], [6, 58, 36, 2, 59, 37], [4, 46, 20, 6, 47, 21], [7, 42, 14, 4, 43, 15],
    [4, 133, 107], [8, 59, 37, 1, 60, 38], [8, 44, 20, 4, 45, 21], [12, 33, 11, 4, 34, 12],
    [3, 145, 115, 1, 146, 116], [4, 64, 40, 5, 65, 41], [11, 36, 16, 5, 37, 17], [11, 36, 12, 5, 37, 13],
    [5, 109, 87, 1, 110, 88], [5, 65, 41, 5, 66, 42], [5, 54, 24, 7, 55, 25], [11, 36, 12],
    [5, 122, 98, 1, 123, 99], [7, 73, 45, 3, 74, 46], [15, 43, 19, 2, 44, 20], [3, 45, 15, 13, 46, 16],
    [1, 135, 107, 5, 136, 108], [10, 74, 46, 1, 75, 47], [1, 50, 22, 15, 51, 23], [2, 42, 14, 17, 43, 15],
    [5, 150, 120, 1, 151, 121], [9, 69, 43, 4, 70, 44], [17, 50, 22, 1, 51, 23], [2, 42, 14, 19, 43, 15],
    [3, 141, 113, 4, 142, 114], [3, 70, 44, 11, 71, 45], [17, 47, 21, 4, 48, 22], [9, 39, 13, 16, 40, 14],
    [3, 135, 107, 5, 136, 108], [3, 67, 41, 13, 68, 42], [15, 54, 24, 5, 55, 25], [15, 43, 15, 10, 44, 16],
    [4, 144, 116, 4, 145, 117], [17, 68, 42], [17, 50, 22, 6, 51, 23], [19, 46, 16, 6, 47, 17],
    [2, 139, 111, 7, 140, 112], [17, 74, 46], [7, 54, 24, 16, 55, 25], [34, 37, 13],
    [4, 151, 121, 5, 152, 122], [4, 75, 47, 14, 76, 48], [11, 54, 24, 14, 55, 25], [16, 45, 15, 14, 46, 16],
    [6, 147, 117, 4, 148, 118], [6, 73, 45, 14, 74, 46], [11, 54, 24, 16, 55, 25], [30, 46, 16, 2, 47, 17],
    [8, 132, 106, 4, 133, 107], [8, 75, 47, 13, 76, 48], [7, 54, 24, 22, 55, 25], [22, 45, 15, 13, 46, 16],
    [10, 142, 114, 2, 143, 115], [19, 74, 46, 4, 75, 47], [28, 50, 22, 6, 51, 23], [33, 46, 16, 4, 47, 17],
    [8, 152, 122, 4, 153, 123], [22, 73, 45, 3, 74, 46], [8, 53, 23, 26, 54, 24], [12, 45, 15, 28, 46, 16],
    [3, 147, 117, 10, 148, 118], [3, 73, 45, 23, 74, 46], [4, 54, 24, 31, 55, 25], [11, 45, 15, 31, 46, 16],
    [7, 146, 116, 7, 147, 117], [21, 73, 45, 7, 74, 46], [1, 53, 23, 37, 54, 24], [19, 45, 15, 26, 46, 16],
    [5, 145, 115, 10, 146, 116], [19, 75, 47, 10, 76, 48], [15, 54, 24, 25, 55, 25], [23, 45, 15, 25, 46, 16],
    [13, 145, 115, 3, 146, 116], [2, 74, 46, 29, 75, 47], [42, 54, 24, 1, 55, 25], [23, 45, 15, 28, 46, 16],
    [17, 145, 115], [10, 74, 46, 23, 75, 47], [10, 54, 24, 35, 55, 25], [19, 45, 15, 35, 46, 16],
    [17, 145, 115, 1, 146, 116], [14, 74, 46, 21, 75, 47], [29, 54, 24, 19, 55, 25], [11, 45, 15, 46, 46, 16],
    [13, 145, 115, 6, 146, 116], [14, 74, 46, 23, 75, 47], [44, 54, 24, 7, 55, 25], [59, 46, 16, 1, 47, 17],
    [12, 151, 121, 7, 152, 122], [12, 75, 47, 26, 76, 48], [39, 54, 24, 14, 55, 25], [22, 45, 15, 41, 46, 16],
    [6, 151, 121, 14, 152, 122], [6, 75, 47, 34, 76, 48], [46, 54, 24, 10, 55, 25], [2, 45, 15, 64, 46, 16],
    [17, 152, 122, 4, 153, 123], [29, 74, 46, 14, 75, 47], [49, 54, 24, 10, 55, 25], [24, 45, 15, 46, 46, 16],
    [4, 152, 122, 18, 153, 123], [13, 74, 46, 32, 75, 47], [48, 54, 24, 14, 55, 25], [42, 45, 15, 32, 46, 16],
    [20, 147, 117, 4, 148, 118], [40, 75, 47, 7, 76, 48], [43, 54, 24, 22, 55, 25], [10, 45, 15, 67, 46, 16],
    [19, 148, 118, 6, 149, 119], [18, 75, 47, 31, 76, 48], [34, 54, 24, 34, 55, 25], [20, 45, 15, 61, 46, 16]
  ]
  const idx = errorCorrectLevel * 40 + typeNumber - 1
  return tbl[idx]
}

// 伽罗瓦域多项式类，用于 Reed-Solomon 纠错编码的运算
class QRPolynomial {
  // 构造函数：去除前导零后，可选择右移（增加更高次项）
  constructor(num, shift) {
    if (!num.length) throw new Error()
    let offset = 0
    while (offset < num.length && num[offset] === 0) offset++
    this.num = new Array(num.length - offset + shift)
    for (let i = 0; i < num.length - offset; i++) this.num[i] = num[i + offset]
  }
  get(index) { return this.num[index] }
  get length() { return this.num.length }
  // 多项式乘法（在伽罗瓦域 GF(256) 上进行）
  multiply(e) {
    const num = new Array(this.length + e.length - 1)
    for (let i = 0; i < this.length; i++) {
      for (let j = 0; j < e.length; j++) {
        num[i + j] ^= galMul(this.get(i), e.get(j))
      }
    }
    return new QRPolynomial(num, 0)
  }
  // 多项式取模（用于 RS 编码，求余数作为纠错码）
  mod(e) {
    if (this.length - e.length < 0) return this
    const ratio = galLog(this.get(0)) - galLog(e.get(0))
    const num = this.num.slice()
    for (let i = 0; i < e.length; i++) num[i] ^= galMul(e.get(i), galExp(ratio))
    return new QRPolynomial(num, 0).mod(e)
  }
}

// 伽罗瓦域 GF(256) 的指数表和对数表，用于加速域内运算
const EXP_TABLE = new Array(256)
const LOG_TABLE = new Array(256)
for (let i = 0; i < 8; i++) EXP_TABLE[i] = 1 << i
for (let i = 8; i < 256; i++) EXP_TABLE[i] = EXP_TABLE[i - 4] ^ EXP_TABLE[i - 5] ^ EXP_TABLE[i - 6] ^ EXP_TABLE[i - 8]
for (let i = 0; i < 255; i++) LOG_TABLE[EXP_TABLE[i]] = i

// 伽罗瓦域 GF(256) 上的对数运算
function galLog(a) { if (a < 1) throw new Error(); return LOG_TABLE[a] }
// 伽罗瓦域 GF(256) 上的指数运算
function galExp(a) { while (a < 0) a += 255; while (a > 255) a -= 255; return EXP_TABLE[a] }
// 伽罗瓦域 GF(256) 上的乘法运算
function galMul(a, b) { if (a === 0 || b === 0) return 0; return EXP_TABLE[LOG_TABLE[a] + LOG_TABLE[b]] }

// 生成 Reed-Solomon 纠错码生成多项式
// ecCount: 纠错码字节数
function rsGenPoly(ecCount) {
  const poly = new QRPolynomial([1], 0)
  for (let i = 0; i < ecCount; i++) {
    poly = poly.multiply(new QRPolynomial([1, galExp(i)], 0))
  }
  return poly
}

// 对数据进行 Reed-Solomon 编码，返回纠错码字节数组
// data: 输入数据字节数组, ecCount: 需要生成的纠错码字节数
function rsEncode(data, ecCount) {
  if (data.length - ecCount <= 0) return
  const poly = new QRPolynomial(data, 0)
  const mod = poly.mod(rsGenPoly(ecCount))
  const result = new Array(ecCount)
  for (let i = 0; i < ecCount; i++) {
    result[i] = mod.get(i + mod.length - ecCount) || 0
  }
  return result
}

// 生成二维码矩阵（二维 0/1 数组），作为绘制二维码的输入
// @param {string} str - 要编码的文本内容
// @param {number} errorCorrectLevel - 纠错等级，默认 QR_ERROR.M
// @returns {number[][]} 尺寸为 (4*typeNumber+17) 的二维 0/1 矩阵
export function generateQRMatrix(str, errorCorrectLevel = QR_ERROR.M) {
  const typeNumber = Math.min(40, Math.max(1, getTypeNumber(str, errorCorrectLevel)))
  const data = getData(str, typeNumber, errorCorrectLevel)
  return buildMatrix(typeNumber, errorCorrectLevel, data)
}

// 根据输入文本长度和纠错等级，确定所需的最小 QR 版本号（1-40）
function getTypeNumber(str, ecl) {
  const lengths = [
    [0, 0, 0, 0], [17, 14, 11, 7], [32, 26, 20, 14], [53, 42, 32, 24], [78, 62, 46, 34],
    [106, 84, 60, 44], [134, 106, 74, 58], [154, 122, 86, 68], [192, 152, 108, 84],
    [230, 180, 130, 98], [271, 213, 151, 119], [321, 251, 177, 137], [367, 287, 203, 155],
    [425, 331, 241, 177], [458, 362, 258, 194], [520, 412, 292, 220], [586, 450, 322, 250],
    [644, 504, 364, 280], [718, 560, 394, 310], [792, 624, 442, 338], [858, 666, 482, 382],
    [929, 711, 509, 403], [1003, 779, 565, 439], [1091, 857, 611, 461], [1171, 911, 661, 511],
    [1273, 997, 715, 535], [1367, 1059, 751, 593], [1465, 1125, 805, 625], [1528, 1190, 868, 658],
    [1628, 1264, 908, 698], [1732, 1370, 982, 742], [1840, 1452, 1030, 790],
    [1952, 1538, 1112, 842], [2068, 1628, 1168, 898], [2188, 1722, 1228, 958],
    [2303, 1809, 1283, 983], [2431, 1911, 1351, 1051], [2563, 1989, 1423, 1093],
    [2699, 2099, 1499, 1139], [2809, 2213, 1579, 1219], [2953, 2331, 1663, 1273]
  ]
  for (let t = 1; t <= 40; t++) {
    const len = lengths[t][ecl]
    const bits = getDataLen(t, QR_MODE.MODE_8BIT_BYTE)
    if (str.length * 8 + 4 + bits <= len) return t
  }
  return 1
}

// 获取指定版本和模式下的字符数长度字段的位数
function getDataLen(typeNumber, mode) {
  const bits = [0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8]
  const bits8 = [0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8, 8]
  if (mode === QR_MODE.MODE_8BIT_BYTE) return bits8[typeNumber]
  return bits[typeNumber]
}

// 对输入字符串进行编码，添加模式指示符、字符计数、数据位、终结符和填充字节，
// 最后进行 RS 纠错编码并交错排列，返回最终的数据字节数组
function getData(str, typeNumber, errorCorrectLevel) {
  const buf = []
    // 模式指示符：0100 表示 8 位字节模式
  buf.push(0, 1, 0, 0)
  // Character count
  const lenBits = getDataLen(typeNumber, QR_MODE.MODE_8BIT_BYTE)
  const countBits = str.length.toString(2).padStart(lenBits, '0')
  for (const c of countBits) buf.push(parseInt(c))
  // Data bytes
  for (let i = 0; i < str.length; i++) {
    const code = str.charCodeAt(i)
    const bin = code.toString(2).padStart(8, '0')
    for (const c of bin) buf.push(parseInt(c))
  }
  // Terminator
  for (let i = 0; i < 4; i++) buf.push(0)
  // Pad to byte
  while (buf.length % 8 !== 0) buf.push(0)
  // Pad to capacity
  const maxBits = getMaxDataBits(typeNumber, errorCorrectLevel)
  while (buf.length < maxBits) {
    buf.push(1, 1, 1, 0, 1, 1, 0, 0) // 236
    if (buf.length >= maxBits) break
    buf.push(0, 0, 0, 1, 0, 0, 0, 1) // 17
  }
  // Convert to bytes
  const bytes = []
  for (let i = 0; i < buf.length; i += 8) {
    let byte = 0
    for (let j = 0; j < 8; j++) byte = (byte << 1) | buf[i + j]
    bytes.push(byte)
  }
  // RS block split + EC
  const rsBlocks = getRSECCBlocks(typeNumber, errorCorrectLevel)
  const totalDataCount = rsBlocks.reduce((s, b) => s + b[0], 0)
  if (bytes.length > totalDataCount) bytes.length = totalDataCount
  const dataBlocks = []
  let offset = 0
  for (const [count, total, ec] of rsBlocks) {
    dataBlocks.push({
      data: bytes.slice(offset, offset + total),
      ec: rsEncode(bytes.slice(offset, offset + total), ec) || []
    })
    offset += total
  }
  // Interleave data
  const maxLen = Math.max(...dataBlocks.map(b => b.data.length))
  const result = []
  for (let i = 0; i < maxLen; i++) {
    for (const block of dataBlocks) {
      if (i < block.data.length) result.push(block.data[i])
    }
  }
  for (let i = 0; i < dataBlocks[0].ec.length; i++) {
    for (const block of dataBlocks) {
      if (i < block.ec.length) result.push(block.ec[i])
    }
  }
  return result
}

// 计算指定版本和纠错等级下，可容纳的最大数据位数
function getMaxDataBits(typeNumber, errorCorrectLevel) {
  const rsBlocks = getRSECCBlocks(typeNumber, errorCorrectLevel)
  return rsBlocks.reduce((s, b) => s + b[0], 0) * 8
}

// 根据版本编码、纠错等级和数据字节，构建完整的二维码矩阵（含所有功能图案和数据）
// 返回经过最优掩码处理后的二维 0/1 数组
function buildMatrix(typeNumber, errorCorrectLevel, data) {
  const modules = []
  const size = typeNumber * 4 + 17
  for (let row = 0; row < size; row++) {
    modules[row] = []
    for (let col = 0; col < size; col++) modules[row][col] = null
  }

  // 放置定位图案（Finder Pattern）及其分隔符
  for (let i = 0; i < 8; i++) {
    for (let j = 0; j < 8; j++) {
      if (i === 7 || j === 7) continue
      if (i < 7 && j < 7) {
        const v = (i === 0 || i === 6 || j === 0 || j === 6 || (i >= 2 && i <= 4 && j >= 2 && j <= 4)) ? 1 : 0
        modules[i][j] = v
        modules[i][size - 1 - j] = v
        modules[size - 1 - i][j] = v
      }
    }
  }

  // 放置对齐图案（Alignment Pattern）
  const positions = PATTERN_POS_TABLE[typeNumber - 1] || []
  for (const p1 of positions) {
    for (const p2 of positions) {
      if (p1 === 6 && p2 === 6) continue
      if (p1 === 6 || (p2 === 6)) continue
      if (modules[p1 - 2] && modules[p1 - 2][p2 - 2] !== undefined) continue
      if (p1 - 2 < 0 || p1 + 2 >= size || p2 - 2 < 0 || p2 + 2 >= size) continue
      for (let r = -2; r <= 2; r++) {
        for (let c = -2; c <= 2; c++) {
          const v = (Math.abs(r) === 2 || Math.abs(c) === 2 || (r === 0 && c === 0)) ? 1 : 0
          if (modules[p1 + r] !== undefined) modules[p1 + r][p2 + c] = v
        }
      }
    }
  }

  // 放置时钟图案（Timing Pattern）：第 6 行和第 6 列交替黑白
  for (let i = 8; i < size - 8; i++) {
    modules[6][i] = i % 2 === 0 ? 1 : 0
    modules[i][6] = i % 2 === 0 ? 1 : 0
  }

  // 暗色模块（Dark Module）：右下角固定为黑色
  modules[size - 8][8] = 1

  // 数据放置：从右下角开始，双列蛇形逐位填入矩阵
  let idx = 0
  for (let col = size - 1; col > 0; col -= 2) {
    if (col <= 6) col--
    for (let row = 0; row < size; row++) {
      for (let c = 0; c < 2; c++) {
        const col2 = col - c
        if (col2 < 0) continue
        const row2 = col % 2 === 0 ? size - 1 - row : row
        if (modules[row2][col2] !== null) continue
        if (idx < data.length) {
          modules[row2][col2] = (data[idx >> 3] >> (7 - (idx & 7))) & 1
          idx++
        } else {
          modules[row2][col2] = 0
        }
      }
    }
  }

  // 尝试 8 种掩码模式，评估每种得分，选取最优掩码
  const bestMask = { score: Infinity, mask: 0, modules: null }
  for (let mask = 0; mask < 8; mask++) {
    const masked = modules.map(row => [...row])
    for (let r = 0; r < size; r++) {
      for (let c = 0; c < size; c++) {
        if (masked[r][c] === null) continue
        let cond = false
        switch (mask) {
          case 0: cond = (r + c) % 2 === 0; break
          case 1: cond = r % 2 === 0; break
          case 2: cond = c % 3 === 0; break
          case 3: cond = (r + c) % 3 === 0; break
          case 4: cond = (Math.floor(r / 2) + Math.floor(c / 3)) % 2 === 0; break
          case 5: cond = (r * c) % 2 + (r * c) % 3 === 0; break
          case 6: cond = ((r * c) % 2 + (r * c) % 3) % 2 === 0; break
          case 7: cond = ((r * c) % 3 + (r + c) % 2) % 2 === 0; break
        }
        if (cond) masked[r][c] = masked[r][c] ? 0 : 1
      }
    }
    // 放置格式信息（纠错等级 + 掩码编号的 BCH 编码）
    const fmt = getBCHTypeInfo((errorCorrectLevel << 3) | mask)
    for (let i = 0; i < 15; i++) {
      const v = (fmt >> i) & 1
      if (i < 6) { masked[i][8] = v }
      else if (i < 8) { masked[i + 1][8] = v }
      else { masked[size - 15 + i][8] = v }
      if (i < 8) { masked[8][size - 1 - i] = v }
      else if (i < 9) { masked[8][15 - i - 1 + 1] = v }
      else { masked[8][15 - i - 1] = v }
    }
    masked[size - 8][8] = 1

    // 评估掩码质量分数（规则 1：连续同色模块惩罚）
    let score = 0
    for (let r = 0; r < size; r++) {
      let run = 0, prev = -1
      for (let c = 0; c < size; c++) {
        if (masked[r][c] === prev) { run++ } else { run = 1; prev = masked[r][c] }
        if (run >= 6) score += run + 3
      }
    }
    for (let c = 0; c < size; c++) {
      let run = 0, prev = -1
      for (let r = 0; r < size; r++) {
        if (masked[r][c] === prev) { run++ } else { run = 1; prev = masked[r][c] }
        if (run >= 6) score += run + 3
      }
    }
    // 规则 2：2x2 同色方块惩罚
    for (let r = 0; r < size - 1; r++) {
      for (let c = 0; c < size - 1; c++) {
        const v = masked[r][c]
        if (v === masked[r + 1][c] && v === masked[r][c + 1] && v === masked[r + 1][c + 1]) {
          score += 3
        }
      }
    }
    // 规则 3：黑白比例失衡惩罚
    const dark = masked.reduce((s, row) => s + row.reduce((s2, v) => s2 + (v === 1 ? 1 : 0), 0), 0)
    const percent = dark / (size * size) * 100
    const diff = Math.abs(percent - 50)
    score += Math.floor(diff / 5) * 10

    if (score < bestMask.score) {
      bestMask.score = score
      bestMask.mask = mask
      bestMask.modules = masked
    }
  }

  return bestMask.modules
}

// Canvas 渲染函数（uni-app 兼容）
export function drawQRCode(canvasId, context, data, size) {
  const modules = generateQRMatrix(data)
  if (!modules || !modules.length) return

  const moduleCount = modules.length
  const cellSize = Math.floor(size / moduleCount)
  const offset = Math.floor((size - cellSize * moduleCount) / 2)

  context.setFillStyle('#ffffff')
  context.fillRect(0, 0, size, size)
  context.setFillStyle('#000000')

  for (let row = 0; row < moduleCount; row++) {
    for (let col = 0; col < moduleCount; col++) {
      if (modules[row][col]) {
        context.fillRect(offset + col * cellSize, offset + row * cellSize, cellSize, cellSize)
      }
    }
  }
  context.draw()
}
