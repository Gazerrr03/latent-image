import Foundation
import Vision
import ImageIO

var records: [[String: Any]] = []
for path in CommandLine.arguments.dropFirst() {
    let url = URL(fileURLWithPath: path)
    guard let source = CGImageSourceCreateWithURL(url as CFURL, nil),
          let image = CGImageSourceCreateImageAtIndex(source, 0, nil) else {
        fputs("Cannot read \(path)\n", stderr); exit(1)
    }
    let width = Double(image.width), height = Double(image.height)
    let request = VNDetectFaceLandmarksRequest()
    try VNImageRequestHandler(cgImage: image, options: [:]).perform([request])
    guard let face = request.results?.max(by: { $0.boundingBox.width * $0.boundingBox.height < $1.boundingBox.width * $1.boundingBox.height }),
          let landmarks = face.landmarks else {
        records.append(["path":path, "error":"no face landmarks"]); continue
    }
    func points(_ region: VNFaceLandmarkRegion2D?) -> [[Double]] {
        guard let region = region else { return [] }
        return region.normalizedPoints.map { p in
            [(face.boundingBox.minX + p.x * face.boundingBox.width) * width,
             (1 - face.boundingBox.minY - p.y * face.boundingBox.height) * height]
        }
    }
    func mean(_ ps: [[Double]]) -> [Double] {
        guard !ps.isEmpty else { return [] }
        return [ps.map{$0[0]}.reduce(0,+)/Double(ps.count), ps.map{$0[1]}.reduce(0,+)/Double(ps.count)]
    }
    let le = points(landmarks.leftEye), re = points(landmarks.rightEye)
    let nose = points(landmarks.nose), lips = points(landmarks.outerLips)
    let contour = points(landmarks.faceContour)
    records.append(["path":path,"width":width,"height":height,"confidence":Double(face.confidence),
                    "leftEye":mean(le),"rightEye":mean(re),"nose":mean(nose),"mouth":mean(lips),
                    "chin":contour.max(by:{$0[1] < $1[1]}) ?? [],
                    "regions":["leftEye":le,"rightEye":re,"nose":nose,"lips":lips,"contour":contour]])
}
let data = try JSONSerialization.data(withJSONObject: records, options:[.prettyPrinted,.sortedKeys])
FileHandle.standardOutput.write(data)

