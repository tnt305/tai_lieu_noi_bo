# Trợ giúp:Lỗi CS1

Trang trợ giúp này là một hướng dẫn.Nó là một hướng dẫn chi tiết các cách thực hiện quy chuẩn của Wikipedia và không phải là quy định, bởi vì nó chưa được cộng đồng xem xét một cách kỹ lưỡng. |

Trang này mô tả các thông báo lỗi của Văn phong Chú thích 1 và Chú thích kiểu 2, ý nghĩa và cách thức giải quyết chúng.

Trước năm 2013, các bản mẫu chú thích sử dụng `{{Chú thích/nhân}}`

làm bản mẫu cơ sở (hiện tại vẫn còn một vài chú thích sử dụng bản mẫu này, ví dụ `{{Chú thích GNIS}}`

). Nhưng trong năm 2013, là một phần của dự án WP:LUA, các biên tập viên Wikipedia đã nâng cấp loạt bản mẫu CS1|2 chuyển sang dùng duy nhất một Mô đun Lua. Mô đun:Citation/CS1 là công cụ kiểm soát cách hiển thị của các chú thích CS1|2 và các dữ liệu chú thích được chuyển đến các công cụ bên ngoài thông qua metadata COinS . Lợi ích của việc nâng cấp là nâng cao hiệu suất, giảm độ phức tạp, dư thừa; và cho mục đích của trang này, cải thiện việc phát hiện lỗi, phân loại và báo cáo.

Thể loại:Lỗi CS1 là thể loại lỗi chung và Thể loại:Bảo trì CS1 là thể loại bảo trì.

Chú ý: những bản mẫu vẫn dùng định dạng cũ chưa chuyển sang dùng mô đun sẽ được ~~gạch ngang~~.

## Kiểm soát hiển thị thông báo lỗi

Trong khi hầu hết các thông báo lỗi của chú thích CS1|2 đều được hiển thị cho người đọc, một số vẫn bị ẩn. Các biên tập viên muốn xem tất cả thông báo lỗi CS1|2 có thể làm như vậy bằng cách cập nhật trang common CSS hoặc trang skin CSS của mình (tương ứng tại common.css và skin.css) bằng các lệnh sau:

```
.mw-parser-output span.cs1-maint {display: inline;} /* hiện tất cả thông báo lỗi Chú thích kiểu 1 */
```

Ngay cả khi cài đặt css này, các trang cũ trong bộ đệm của Wikipedia cũng có thể chưa được cập nhật để hiển thị các thông báo lỗi này dù được liệt kê vào thể loại theo dõi. WP:NULLEDIT sẽ giải quyết vấn đề này.

Các biên tập viên nếu không muốn thấy bất kỳ thông báo lỗi CS1 nào có thể ẩn tất cả bằng cách cập nhật trang common hay skin CSS của mình bằng lệnh:

```
.mw-parser-output span.cs1-visible-error {display: none;} /* ẩn tất cả thông báo lỗi Chú thích kiểu 1 */
```

## |ngày truy cập= cần |url=

`|ngày truy cập=`

cần `|url=`

(thông báo lỗi được mặc định ẩn)

`|ngày truy cập=`

(hoặc biệt danh của nó, `|access-date=`

) là ngày mà nguồn chú thích `|url=`

được thêm vào bài viết. Nếu `|ngày truy cập=`

được sử dụng mà không có `|url=`

thì thông báo này sẽ xuất hiện. Nếu chú thích không sử dụng liên kết mạng thì `|ngày truy cập=`

là dư thừa và cần được xóa.

Để giải quyết lỗi này, bổ sung giá trị cho `|url=`

hoặc xóa `|ngày truy cập=`

. Biên tập viên hãy cố gắng xác định nguyên nhân dẫn đến việc chú thích có `|ngày truy cập=`

mà không có `|url=`

. Ví dụ, chú thích có thể là chưa bao giờ có `|url=`

hoặc `|url=`

đã bị xóa do liên kết tới trang web vi phạm bản quyền (xem WP:COPYLINK ) hoặc `|url=`

bị coi là đã hỏng (nhầm lẫn) và loại bỏ. Nếu chú thích chưa từng có `|url=`

hoặc bị xóa vì vi phạm bản quyền, hãy xóa `|ngày truy cập=`

. Khi `|url=`

đã hỏng bị xóa, hãy cố gắng khôi phục nó nếu có thể, nếu không được hãy xóa `|ngày truy cập=`

.

Các trang có lỗi này được tự động xếp vào Thể loại:Lỗi CS1: ngày truy cập thiếu URL.[a]

## |archive-url= is malformed

`|archive-url=`

is malformed: <reason> (thông báo lỗi được mặc định ẩn)

Archive.org cho phép truy cập tới trang lưu trữ bằng nhiều dạng url khác nhau. Một số có thể được kể đến là:

`https://web.archive.org/web/YYYYMMDD`

– lưu nhanh; đây là hình thứchhmmss/http://www.trang-web-vi-du.com **thường được sử dụng**cho tham số`|url lưu trữ=`

.`https://web.archive.org/web/*/http://`

trang kết quả tìm kiếm các trang đã được lưu nhanh;www.trang-web-vi-du.com **không phù hợp**để dùng làm chú thích.`https://web.archive.org/web/`

– nhãn thời gian không đầy đủ; archive.org trả về kết quả lưu trữ gần nhất.201603/http://www.trang-web-vi-du.com `https://web.archive.org/save/http://`

– lưu phiên bản hiện tại của trang mục tiêu;www.trang-web-vi-du.com **không sử dụng**định dạng này.

Có hai dạng url cơ bản:

`https://web.archive.org/<`

– dạng cũ*timestamp*>/...`https://web.archive.org/`

– dạng mới**web/**<*timestamp*><*flags*>/...

Thông báo lỗi thường có lý do kèm theo; chúng có thể là:

- save command – url của archive.org là lệnh lưu.
- path –
**web/**was expected but something else was found - timestamp – nhãn thời gian không phải là 14 chữ số
- flag – the flag portion of the url path (if present; new form urls only) is not 2 lowercase letters followed by an underscore: 'id_'
- liveweb –
`liveweb.archive.org`

is a deprecated form of the domain name.

Khi url của archive.org có bất kỳ lỗi nào trong số những lỗi này, Mô đun:Citation/CS1 sẽ không liên kết tới archive.org và sẽ hiện một thông báo lỗi thích hợp.

Để giải quyết lỗi này, chọn một url của một trang thích hợp đã được lưu trữ tại archive.org. Tìm kiếm url đích.

Các trang có lỗi này được tự động xếp vào Thể loại:Lỗi CS1: URL lưu trữ.[a]

## |url lưu trữ= cần |ngày lưu trữ=

`|url lưu trữ=`

cần `|ngày lưu trữ=`


`|ngày lưu trữ=`

(hay các biệt danh của nó, `|archive-date=`

), xác định ngày mà tài nguyên được lưu trữ.

Để giải quyết lỗi này, cung cấp một giá trị cho `|ngày lưu trữ=`

. Với tài nguyên web được lưu trữ tại archive.org,[1] ngày lưu trữ có thể được tìm thấy trong `|url lưu trữ=`

; với tài nguyên web được lưu trữ tại webcitation.org,[2] thời gian cache nằm trong header trang lưu trữ.

Các trang có lỗi này được tự động xếp vào Thể loại:Lỗi CS1: URL lưu trữ.[a]

## |url lưu trữ= cần |url=

`|url lưu trữ=`

cần `|url=`


Một chú thích có các tham số `|url lưu trữ=`

và `|ngày lưu trữ=`

bắt buộc phải có `|url=`

. Khi có `|url-status=dead`

, thứ tự các siêu liên kết trong chú thích sẽ thay đổi và hiện url lưu trữ lên trước.

Để giải quyết lỗi này, bổ sung giá trị cho tham số `|url=`

. Đối với tài nguyên mạng được lưu trữ tại archive[1] url gốc có thể được tìm thấy trong giá trị của `|url lưu trữ=`

; đối với tài nguyên được lưu trữ tại webcitation[2] url gốc được thể hiện ở phần tiêu đề của trang lưu trữ.

Các trang có lỗi này được tự động xếp vào Thể loại:Lỗi CS1: URL lưu trữ.[a]

## Kiểm tra giá trị |arxiv=

Kiểm tra giá trị `|arxiv=`


Chú thích `{{cite arxiv}}`

[b] yêu cầu 1 chứ không phải cả 2 tham số `|arxiv=`

và `|eprint=`

.

Để giải quyết lỗi này, hãy đảm bảo rằng tham số `|arxiv=`

hoặc `|eprint=`

được đặt đúng giá trị.

Các trang có lỗi này được tự động xếp vào Thể loại:Lỗi CS1: arXiv.[a]

## |chương= bị bỏ qua

`|chương=`

bị bỏ qua

Các bản mẫu Văn phong Chú thích 1 như `{{chú thích web}}`

, `{{chú thích báo}}`

, `{{chú thích tạp chí}}`

, `{{chú thích thông cáo báo chí}}`

, , `{{cite podcast}}`

, cũng như `{{chú thích nhóm tin}}`

`{{chú thích}}`

khi sử dụng tham số `|work=`

hay bất kỳ biệt danh nào của nó (`|periodical=`

, `|journal=`

, `|tạp chí=`

, `|newspaper=`

, `|báo=`

, `|magazine=`

, `|work=`

, `|tác phẩm=`

, `|công trình=`

, `|website=`

, `|periodical=`

, `|encyclopedia=`

, `|encyclopaedia=`

, `|bách khoa toàn thư=`

, `|bách khoa thư=`

, `|từ điển bách khoa=`

, `|dictionary=`

, `|từ điển=`

, `|tự điển=`

), không sử dụng `|chương=`

hay biệt danh `|contribution=`

, `|entry=`

, `|article=`

, `|section=`

, `|chapter=`

và `|mục=`

.

Để giải quyết lỗi này:

- Sử dụng bản mẫu chú thích phù hợp hơn, hoặc
- đặt nội dung của tham số
`|chương=`

trong`|tiêu đề=`

, hoặc - trong {{chú thích báo}}, tham số
`|department=`

có thể được dùng để đặt tên cho mục của tờ báo (VD: Obituaries)

Các trang có lỗi này được tự động xếp vào Thể loại:Lỗi CS1: chương bị bỏ qua.[a]

## Kiểm tra giá trị |arxiv=

Kiểm tra giá trị `|arxiv=`


Khi bản mẫu chú thích có chứa tham số `|arxiv=`

, Mô đun sẽ kiểm tra để xác định xem mã định danh arXiv có phù hợp hay không.[3] Mã định danh yêu cầu số id bài viết hợp lệ; giá trị năm và tháng hợp lệ; dấu gạch ngang, gạch chéo và chấm được đặt đúng cách.

Để giải quyết lỗi này, hãy xác định rằng giá trị tham số `|arxiv=`

là chính xác.

Các trang có lỗi này được tự động xếp vào Thể loại:Lỗi CS1: arXiv.[a]

## Kiểm tra giá trị |asin=

Kiểm tra giá trị `|asin=`


Khi bản mẫu chú thích có chứa tham số `|asin=`

, Mô đun sẽ kiểm tra để xác định xem mã định danh ASIN có đúng là chứa mười ký tự bao gồm chữ viết hoa và số, không có dấu câu hay dấu cách hay không; nếu ký tự đầu tiên là số, thì mã ASIN này phải tuân thủ quy tắc của mã ISBN 10 số.

Để giải quyết lỗi này, hãy đảm bảo rằng giá trị của `|asin=`

là chính xác.

Nếu giá trị của `|asin=`

là chính xác và đều là số, sử dụng `|isbn=`

thay cho tham số này và xóa mọi tham số `|asin-tld=`

. Các bài viết có chú thích CS1 sử dụng `|asin=`

với giá trị đều là số được phân loại trong Thể loại:Bảo trì CS1: ASIN sử dụng ISBN.

Các trang có lỗi này được tự động xếp vào Thể loại:Lỗi CS1: ASIN.[a]

## Kiểm tra giá trị |bibcode= <message>

Kiểm tra giá trị `|bibcode=`

<message>

Khi bản mẫu chú thích có chứa tham số `|bibcode=`

, Mô đun sẽ kiểm tra để xác định xem mã định danh bibcode có được định dạng đúng hay không.[4] Mã Bibcode phải thỏa mãn các yêu cầu sau:

- độ dài phải là 19 ký tự (<message> = 'length')
- vị trí kí tự:
- 1-4 là một số nằm trong phạm vi 1000 – 2026 (<message> = 'year')
- 5 là một chữ cái
- 6-8 là chữ cái, ký tự và (&) hoặc dấu chấm (ký tự và (&) không thể đứng trước dấu chấm) (<message> = 'journal')
- 9 là một chữ cái hoặc dấu chấm
- 10-18 là chữ cái, chữ số hoặc dấu chấm
- 19 là chữ cái hoặc dấu chấm


Để giải quyết lỗi này, hãy đảm bảo rằng giá trị của `|bibcode=`

là chính xác.

Các trang có lỗi này được tự động xếp vào Thể loại:Lỗi CS1: bibcode.[a]

## Kiểm tra giá trị |biorxiv=

Kiểm tra giá trị `|biorxiv=`


Khi bản mẫu chú thích có chứa tham số `|biorxiv=`

, Mô đun sẽ kiểm tra để xác định xem mã định danh bioRxiv có bao gồm sáu ký tự số, không có dấu câu hay dấu cách hay không. Một lỗi thường gặp là biên tập viên nhập cả *url* của bioRxiv (https://dx.doi.org/10.1101/<BIORXIV>), hoặc *doi* của bioRxiv (10.1101/<BIORXIV>).

Để giải quyết lỗi này, hãy đảm bảo rằng giá trị của `|biorxiv=`

là chính xác.

Các trang có lỗi này được tự động xếp vào Thể loại:Lỗi CS1: bioRxiv.[a]

## Kiểm tra giá trị |citeseerx=

Kiểm tra giá trị `|citeseerx=`


Khi bản mẫu chú thích có chứa tham số `|citeseerx=`

, Mô đun sẽ kiểm tra để xác định xem mã định danh CiteSeerX có được định dạng phù hợp hay không.

Mã định danh CiteSeerX là mã được gán cho `?doi=`

trong URL của tài liệu CiteSeerX. (Đừng nhầm lẫn với mã Digital object identifier (DOI): **đừng** nhập vào tham số `|doi=`

.)

Ví dụ: nếu bạn muốn liên kết tới `http://citeseerx.ist.psu.edu/viewdoc/summary?doi=10.1.1.220.7880`

, **hãy** dùng cú pháp `|citeseerx=10.1.1.220.7880`

.

Các trang có lỗi này được tự động xếp vào Thể loại:Lỗi CS1: citeseerx.[a]

## Kiểm tra giá trị ngày tháng trong: |<param1>=, |<param2>=, ...

Kiểm tra giá trị ngày tháng trong: `|<param1>=, |<param2>=, ...`


Khi bản mẫu chú thích có chứa tham số ngày (`|ngày truy cập=`

, `|ngày lưu trữ=`

,...), Mô đun sẽ kiểm tra để xác định xem giá trị của tham số ngày đó có phù hợp với Cẩm nang biên soạn của Wikipedia hay không. Xem .

Để giải quyết lỗi này, hãy đảm bảo rằng ngày được nhập vào là một ngày có thực, không ở trong tương lai và được định dạng theo Cẩm nang biên soạn của Wikipedia. Xem bảng một vài ví dụ về ngày không được chấp nhận và cách sửa chúng bên dưới. Hoặc, một số vấn đề bạn đang tìm:

- Ngày không thể xuất hiện (ví dụ, 29 tháng 2 năm 2011)
`|ngày truy cập=`

cần cả ngày, không phải chỉ tháng và năm- Đặt sai vị trí, không chính xác, hoặc dấu phân tách không hợp lệ
- Sử dụng dấu gạch ngang hoặc gạch chéo khi viết khoảng thời gian (phải dùng dấu gạch nối)
- Viết sai chính tả, hoặc viết hoa không đúng
- Các định dạng ngày không được chấp nhận tại Wikipedia
- Nhập vào nhiều hơn một giá trị ngày trong tham số ngày
- Không chấp nhận các năm trước năm 100 sau Công nguyên.

Không sử dụng ` `

, `–`

, hay `{{spaced ndash}}`

vì chúng làm hỏng metadata, thay vào đó hãy sử dụng dấu gạch ngang "-". Ngày tương lai trong tham số `|date=`

bị giới hạn đến năm hiện tại +1; nghĩa là, vào năm 2025, `|date=`

chấp nhận ngày trong năm 2026, nhưng không chấp nhận ngày trong năm 2027 về sau.

Ngày trước năm 1582 được coi là ngày tính theo lịch Julian, ngày từ năm 1582 trở đi được coi là ngày tính theo lịch Gregorian. Lịch Julian được sử dụng tại một số nơi tới năm 1923, ba ngày 29 tháng 2 năm 1700, 1800, 1900 trong lịch Julian sẽ gây ra thông báo lỗi vì những năm này không phải là năm nhuận trong lịch Gregorian.

Ngày truy cập (`|ngày truy cập=`

) được kiểm tra để đảm bảo rằng nó chứa đầy đủ ngày, tháng, năm và có giá trị sau ngày 15 tháng 1 năm 2001 (ngày thành lập Wikipedia) tới ngày hôm nay +1; vì các biên tập viên có thể ở các múi giờ +1 ngày so với ngày UTC.

Các trang có lỗi này được tự động xếp vào Thể loại:Lỗi CS1: ngày tháng.[a]

| Vấn đề | Không nhận | Chấp nhận |
|---|---|---|
| Tiếng Việt | ||
| Định dạng ngày
"mm-dd-yyyy" hoặc "dd-mm-yyyy" |
`|ngày=07-12-2009` `|ngày=12-07-2009`
|
`|ngày=2009-12-07`
|
| Sử dụng gạch chéo | `|ngày=2009/12/07`
|
`|ngày=2009-12-07`
|
| Mùa | `|ngày=mùa Xuân 2009`
|
`|ngày=2009`
|
| Tháng viết bằng chữ | `|ngày=12 tháng 07 2009`
|
`|ngày=2009-07-12`
|
| Tháng viết bằng chữ | `|ngày=12 tháng bảy 2009`
|
`|ngày=2009-07-12`
|
| Sử dụng gạch nối để chỉ quãng thời gian (phải dùng gạch ngang "–") |
`|ngày=2002-2003`
|
`|ngày=2002–2003`
|
| Ngày tương lai | `|ngày=2102`
|
`|ngày=2012`
|
| Sử dụng liên kết wiki | `|ngày=[[2009]]-12-07`
|
`|ngày=2009-12-07`
|
| Khoảng thời gian | `|ngày=2009-12-07 – 2010-01-13`
|
`|ngày=ngày 17 tháng 12 năm 2009 – ngày 13 tháng 01 năm 2010`
|
| Khoảng thời gian | `|ngày=2009-12 – 2010-01`
|
`|ngày=tháng 12 năm 2009 – tháng 01 năm 2010`
|
| Thiếu dấu cách | `|ngày=ngày 17 tháng 12 năm 2009–ngày 13 tháng 01 năm 2010`
|
`|ngày=ngày 17 tháng 12 năm 2009 – ngày 13 tháng 01 năm 2010`
|
| Tháng hoặc ngày 1 chữ số | `|date=2007-3-6` |
`|date=2007-03-06`
|
| Năm 2 chữ số | `|date=87-12-06` |
`|date=1987-12-06`
|
Tiếng Anh[c]
| ||
| Sử dụng gạch chéo để chỉ quãng thời gian (phải dùng gạch ngang "–") |
`|date=2002/2003` or `|date=July/August, 2003` |
`|date=2002–2003` or `|date=July–August 2003`
|
| Sử dụng gạch nối để chỉ quãng thời gian (phải dùng gạch ngang "–") |
`|date=April-May 2004` |
`|date=April–May 2004`
|
| Thiếu khoảng trống quanh dấu gạch ngang | `|date=April 2003–May 2004` |
`|date=April 2003 – May 2004`
|
| Viết hoa tháng | `|date=28 february 1900` |
`|date=28 February 1900`
|
| Viết hoa tháng | `|date=28 FEBRUARY 1900` |
`|date=28 February 1900`
|
| Viết hoa mùa | `|date=spring 2011` |
`|date=Spring 2011`
|
| Ngày truy cập không thể quá xa trong quá khứ | `|access-date=1 January 2001` |
`|access-date=1 January 2010`
|
| Ngày truy cập chỉ có tháng | `|access-date=January 2015` |
`|access-date=12 January 2015`
|
| Thời gian mơ hồ | `|date=2002-03` |
|
| Viết tắt | `|date=Febr. 28, 1900` |
|
| Ngày không tồn tại | `|date=February 29, 1900` |
|
| Undated | `|date=Undated` |
`|date=n.d.`
|
| Dấu phẩy giữa tháng và năm | `|date=February, 1900` |
`|date=February 1900`
|
| Dấu phẩy sau mùa | `|date=Winter, 1900–1901` |
`|date=Winter 1900–1901`
|
| Thiếu dấu phẩy ở định dạng cần nó | `|date=February 28 1900` |
`|date=February 28, 1900` hoặc`|date=28 February 1900`
|
| Văn bản không phải thời gian | `|date=2008, originally 2000` |
`|date=2008` `|orig-year=2000`
|
| Lót số 0 | `|date=January 04, 1987` |
`|date=January 4, 1987`
|
| Sử dụng gạch chéo | `|date=12/6/87` |
|
| Liên kết Wiki | `|date=[[April 1]], [[1999]] ` |
`|date=April 1, 1999`
|
| Định dạng ngày
"mm-dd-yyyy" hoặc "dd-mm-yyyy" |
`|date=07-12-2009` |
`|date=7 December 2009` or `|date=12 July 2009` or `|date=July 12, 2009` or `|date=December 7, 2009`
|
| Ngày gần đúng hoặc không chắc chắn | `|date=circa 1970` or `|date={{circa}} 1970` |
`|date=c. 1970`
|

## Kiểm tra giá trị |doi=

Kiểm tra giá trị `|doi=`


Khi bản mẫu chú thích có chứa tham số `|doi=`

, Mô đun sẽ kiểm tra để xác định xem phần tiền tố của mã định danh DOI có chứa `10.`

hay không. Ngoài ra giá trị của `|doi=`

còn được kiểm tra để đảm bảo rằng nó không chứa dấu cách hay dấu gạch ngang và không kết thúc bằng dấu chấm câu. Các bước xác nhận thêm của DOI không được thực hiện.

Để giải quyết lỗi này, hãy đảm bảo rằng giá trị của `|doi=`

là chính xác.

Các trang có lỗi này được tự động xếp vào Thể loại:Lỗi CS1: DOI.[a]

## Kiểm tra giá trị |hdl=

Kiểm tra giá trị `|hdl=`


Khi bản mẫu chú thích có chứa tham số `|hdl=`

, Mô đun sẽ kiểm tra để xác định xem giá trị của hdl trông có giống một giá trị đúng hay không. Giá trị của `|hdl=`

được kiểm tra để đảm bảo rằng nó không chứa dấu cách, dấu gạch ngang và không kết thúc bằng dấu chấm câu. Các bước kiểm tra sâu hơn không được thực hiện.

Để giải quyết lỗi này, hãy đảm bảo rằng giá trị của `|hdl=`

là chính xác.

Các trang có lỗi này được tự động xếp vào Thể loại:Lỗi CS1: HDL.[a]

## Kiểm tra giá trị |isbn=

Kiểm tra giá trị `|isbn=`


Khi bản mẫu chú thích có chứa tham số `|isbn=`

sẽ được kiểm tra để đảm bảo rằng mã ISBN có độ dài phù hợp (10 hoặc 13 chữ số), sử dụng dấu tách tùy chọn chính xác (dấu cách đơn hoặc dấu gạch nối) và cuối cùng là kiểm tra các đặc điểm kỹ thuật của ISBN. Tham số này chỉ cho phép nhập duy nhất một mã ISBN, việc nhiều hơn một ký tự hay có một ký tự sai cũng có thể làm hỏng liên kết tới Đặc biệt:Nguồn sách.

Lỗi này có thể bao gồm một hay nhiều lỗi sau:

- độ dài – mã ISBN không phải là 10 hoặc 13 chữ số
- checksum – mã ISBN có một hoặc nhiều chữ số không chính xác; tìm lỗi chính tả và hoán vị
- ký tự không hợp lệ – ISBN có một hoặc nhiều "chữ số" có giá trị không phù hợp với độ dài của ISBN
- tiền tố không hợp lệ – mã ISBN 13 số phải bắt đầu bằng '978' hoặc '979'
- mẫu không hợp lệ – mã ISBN 10 số có ký tự 'X' bị định vị sai

Để giải quyết lỗi này, hãy đảm bảo rằng giá trị của `|isbn=`

là chính xác, rằng trong tham số này chỉ có duy nhất một mã ISBN, các dấu phân cách được sử đặt đúng vị trí và không có ký tự dư thừa. Sử dụng mã ISBN 13 số nếu "có sẵn". Khi sử dụng mã ISBN 10 số, kiểm tra xem chữ 'x' có phải chữ thường hay không, nếu phải hãy thay nó bằng chữ 'X' hoa.

**Đừng**cố giải quyết lỗi bằng cách tính lại số kiểm tra. Số kiểm tra có mặt ở đó để kiểm tra xem phần chính của số đó có đúng không. Nếu ISBN không đúng, có thể đã có một lỗi đánh máy trong phần chính của nó. Trong trường hợp này, việc tính lại số kiểm tra sẽ cho ra một mã hợp lệ nhưng lại dẫn đến một nguồn sai (hoặc chẳng đến đâu cả).- Nếu bạn chỉ có mã ISBN 10 số,
**hãy**sử dụng nó, đừng cố tự chuyển đổi sang mã 13 số. - Nếu mã số được in trong nguồn của bạn không thể xác thực,
**hãy**kiểm tra cả bìa trước và trang bìa lót, không có gì lạ khi ISBN bị in sai ở bìa trước nhưng đúng ở bìa lót. **Hãy**xem trước bản chỉnh sửa của bạn và kiểm tra xem bây giờ mã ISBN mới có liên kết tới nguồn chính xác hay không.

Trong những trường hợp hy hữu, các nhà xuất bản đã xuất bản những cuốn sách có mã ISBN không đúng định dạng. Nếu bạn chắc chắn rằng nhà xuất bản đã không tuân thủ các quy tắc định dạng mã ISBN khi xuất bản, hãy thêm `|ignore-isbn-error=true`

vào chú thích để ngăn việc thông báo lỗi. Trong nhiều trường hợp, bản tái bản của cuốn sách được phát hành với mã sửa lỗi, hãy sử dụng mã sửa lỗi khi có thể.

Đôi khi những số được gán cho `|isbn=`

có vẻ hợp lệ, độ dài đúng, kiểm tra chữ số hợp lệ, nhưng lại không phải là mã ISBN đúng. Công cụ này có thể sẽ hữu ích.

Xem thêm Wikipedia:ISBN .

Các trang có lỗi này được tự động xếp vào Thể loại:Trang có lỗi ISBN.[a]

## Kiểm tra giá trị |ismn=

Kiểm tra giá trị `|ismn`

=

Tham số `|ismn=`

là mã định danh ISMN , Mô đun sẽ kiểm tra để xác định nó có đảm bảo độ dài phù hợp (13 chữ số), các dấu tách tùy chọn chính xác (dấu cách đơn hoặc gạch nối) và kiểm tra các chữ số theo đặc điểm kỹ thuật của ISMN. Tham số `|ismn=`

chỉ cho phép nhập một mã ISMN. Nhập nhiều mã ISMN hoặc dùng các ký tự không phải là một phần của ISMN sẽ làm hỏng metadata COinS.

Để giải quyết lỗi này, hãy đảm bảo rằng giá trị của `|ismn=`

là chính xác, chỉ có một mã ISMN được sử dụng, các dấu tách tùy chọn được sử dụng đúng vị trí và không có ký tự không hợp lệ, mã ISMN chứa đúng 13 chữ số.

Các trang có lỗi này được tự động xếp vào Thể loại:Lỗi CS1: ISMN.[a]

## Kiểm tra giá trị |issn=

- Kiểm tra giá trị
`|issn`

= - Kiểm tra giá trị
`|eissn`

=

Tham số `|issn=`

và `|eissn=`

là mã định danh ISSN, khi một trong hai tham số này được nhập, Mô đun sẽ kiểm tra để xác định xem mã định danh ISSN có độ dài phù hợp (8 chữ số) và chữ số kiểm tra ở vị trí cuối cùng đúng theo thông số kỹ thuật của ISSN. Chỉ một trong hai mã ISSN và eISSN được cho phép vì toàn bộ giá trị của `|issn=`

và `|eissn=`

được bao gồm trong metadata COinS của chú thích. ISSN và eISSN luôn được hiển thị dưới dạng hai số có bốn chữ và được phân tách bằng dấu gạch nối.

Để giải quyết lỗi này, hãy đảm bảo rằng giá trị của `|issn=`

và `|eissn=`

là chính xác, chỉ có các ký tự của mã định danh được nhập vào mà không có ký tự khác (các ký tự được cho phép là 0-9, X và -). Nếu chữ số kiểm tra là chữ 'x' thường, hãy đổi nó thành chữ 'X' hoa.

Các trang có lỗi này được tự động xếp vào Thể loại:Lỗi CS1: ISSN.[a]

## Kiểm tra giá trị |jfm=

Kiểm tra giá trị `|jfm=`


Khi bản mẫu chú thích có chứa tham số `|jfm=`

, Mô đun sẽ kiểm tra để xác định xem giá trị của jfm có giống như một giá trị đúng hay không. Mã định danh `|jfm=`

được kiểm tra để đảm bảo rằng nó có dạng: `nn.nnnn.nn`

trong đó `n`

là số bất kỳ 0-9. Các bước kiểm tra sâu hơn không được thực hiện.

Để giải quyết lỗi này, hãy đảm bảo rằng giá trị của `|jfm=`

là chính xác.

Các trang có lỗi này được tự động xếp vào Thể loại:Lỗi CS1: JFM.[a]

## Kiểm tra giá trị |lccn=

Kiểm tra giá trị `|lccn=`


Tham số `|lccn=`

là mã định danh Số kiểm soát Thư viện Quốc hội Hoa Kỳ. Nó được kiểm tra để đảm bảo rằng có độ dài thích hợp và chữ số đầu tiên hợp lệ.

LCCN là một chuỗi dài 8–12 ký tự. Độ dài của LCCN quyết định loại ký tự của những ký tự đầu tiên 1–3; ký tự thứ tám từ phải sang luôn là một chữ số.[5]

| Độ dài | Mô tả |
|---|---|
| 8 | tất cả các ký tự đều là chữ số |
| 9 | ký tự 1 là chữ thường |
| 10 | 2 ký tự đầu tiên đều là chữ thường hoặc đều là chữ số |
| 11 | ký tự 1 là chữ thường; ký tự 2 và 3 đều là chữ số hoặc đều là chữ thường |
| 12 | 2 ký tự đầu tiên đều là chữ thường |

Các bước xác thực thêm không được thực hiện.

Để giải quyết lỗi này, hãy đảm bảo rằng `|lccn=`

giá trị chính xác, không có chữ cái, dấu câu hay ký tự khác.

Các trang có lỗi này được tự động xếp vào Thể loại:Lỗi CS1: LCCN.[a]

## Kiểm tra giá trị |message-id=

Kiểm tra giá trị `|message-id=`


Tham số `|message-id=`

là mã định danh liên kết với một netnews message.[6] Giá trị của tham số này được kiểm tra để đảm bảo rằng nó chứa `@`

giữa mã định danh trái và phải, và ký tự đầu tiên không phải là `<`

, ký tự cuối cùng không phải là `>`

. Các bước kiểm tra sâu hơn không được thực hiện.

Để giải quyết lỗi này, hãy đảm bảo rằng giá trị của `|message-id=`

là chính xác, rằng giá trị của tham số chứa `@`

và không được đặt trong cặp ngoặc `<...>`

.

Các trang có lỗi này được tự động xếp vào Thể loại:Lỗi CS1: message-id.[a]

## Kiểm tra giá trị |mr=

Kiểm tra giá trị `|mr=`


Khi bản mẫu chú thích có chứa tham số `|mr=`

, Mô đun sẽ kiểm tra để xác định xem giá trị của mã định danh mr có trông giống như một mã đúng hay không. Mã `|mr=`

được kiểm tra để đảm bảo rằng có chỉ chứa các chữ số và có độ dài không quá bảy chữ số. Các bước kiểm tra sâu hơn không được thực hiện.

Để giải quyết lỗi này, hãy đảm bảo rằng giá trị của `|mr=`

là chính xác.

Các trang có lỗi này được tự động xếp vào Thể loại:Lỗi CS1: MR.[a]

## Kiểm tra giá trị |oclc=

Kiểm tra giá trị `|oclc=`


Tham số `|oclc=`

là mã định danh OCLC. Tham số này chỉ cho phép nhập một mã định danh duy nhất. Mã định danh phải thỏa mãn điều kiện sau:

- tiền tố
`ocm`

+ 8 chữ số - tiền tố
`ocn`

+ 9 chữ số - tiền tố
`on`

+ 10 chữ số - tiền tố
`(OCoLC)`

+ một số không có số 0 đứng đầu - số từ 1 đến 10 không có tiền tố

Các bước kiểm tra sâu hơn không được thực hiện.

Để giải quyết lỗi này, hãy đảm bảo rằng giá trị của `|oclc=`

là chính xác.

Mẹo để sửa lỗi này: Biên tập viên đôi khi có thể đặt mã ISBN, LCCN, ASIN hợp lệ, hoặc các mã khác tương tự vào tham số `|oclc=`

.

Các trang có lỗi này được tự động xếp vào Thể loại:Lỗi CS1: OCLC.[a]

## Kiểm tra giá trị |ol=

Kiểm tra giá trị `|ol=`


Tham số `|ol=`

là mã định danh của Open Library . Mã định danh là một hoặc nhiều chữ số, kết thúc chuỗi bằng ký tự `A`

(authors - tác giả), `M`

(books - sách), hay `W`

(works - tác phẩm). Không có xác nhận thêm.

Để giải quyết lỗi này, hãy đảm bảo rằng `|ol=`

có giá trị chính xác. Không chứa "OL" trong giá trị.

Các trang có lỗi này được tự động xếp vào Thể loại:Lỗi CS1: OL.[a]

## Kiểm tra giá trị |<param>-link=

- Kiểm tra giá trị
`|<param>-link=`

- Kiểm tra giá trị
`|<param>=`


Các tham số liên kết và tiêu đề được kết hợp theo cặp để tạo liên kết Wiki tới bài viết liên quan.

|
|

Lỗi này xảy ra khi tham số `|lk <param>=`

chứa liên kết Wiki hoặc liên kết ngoài, hoặc chứa bất kỳ ký tự nào thuộc dạng không được phép có trong tiêu đề bài viết (trừ dấu gạch dưới `_`

được sử dụng thay khoảng trắng, và thăng `#`

được sử dụng để tạo liên kết tới một đề mục trong bài). Các ký tự bị cấm là: `< > [ ] | { }`

.

Giá trị của `|lk <param>=`

chỉ nên chứa tiêu đề của bài viết Wikipedia hoặc liên kết tới một đề mục trong bài viết Wikipedia. Mô đun sẽ kiểm tra `|lk <param>=`

xem có liên kết wiki hay các URI scheme (`http://`

, `https://`

, `//`

,...) hay không.

Để giải quyết lỗi này, hãy dùng một trong các cách sau:

- đảm bảo rằng giá trị của
`|lk <param>=`

là tên đầy đủ của một bài viết Wikipedia (không có dấu ngoặc vuông) hoặc một đề mục của bài viết; và không phải là một liên kết đến trang web ngoài. - đảm bảo rằng không có liên kết wiki trong các tham số
`|<param>=`

tương ứng. - nếu bạn muốn tạo liên kết tới trang web ngoài Wikipedia, hãy sử dụng
`|url=`

hoặc một tham số khác tương tự. - đảm bảo rằng trong các tham số không có các ký tự không hợp lệ.

Các trang có lỗi này được tự động xếp vào Thể loại:Lỗi CS1: liên kết tham số.[a]

## Kiểm tra giá trị |pmc=

Kiểm tra giá trị `|pmc=`


Tham số `|pmc=`

là mã định danh của PubMed Central. Mã PMC là một số thứ tự từ 1 trở lên. Mô đun:Citation/CS1 sẽ kiểm tra để đảm bảo rằng mã PMC là một số tự nhiên lớn hơn 0 và nhỏ hơn 8700000, và không chứa bất kỳ ký tự nào khác. Các bước kiểm tra sâu hơn không được thực hiện.

Để giải quyết lỗi này, hãy đảm bảo rằng giá trị của `|pmc=`

là chính xác, rằng nó không chứa chữ cái, dấu chấm câu hay bất kỳ ký tự nào khác. Đừng nhập "PMC" vào giá trị.

Các trang có lỗi này được tự động xếp vào Thể loại:Lỗi CS1: PMC.[a]

Cập nhật khoảng giá trị cho phép tại Mô đun:Citation/CS1/Configuration.

## Kiểm tra giá trị |pmid=

Kiểm tra giá trị `|pmid=`


Tham số `|pmid=`

là mã định danh PubMed. Mã định danh này sẽ được kiểm tra để đảm bảo rằng nó là một số có giá trị từ 1 tới 30000000, không chứa dấu chấm câu hay dấu cách.

Để giải quyết lỗi này, hãy đảm bảo rằng giá trị của `|pmid=`

là chính xác. Nếu bạn tìm thấy một thứ gì đó trông giống như một mã PMID nhưng bắt đầu bằng "PMC", hãy sử dụng `|pmc=`

thay vì `|pmid=`

.

Các trang có lỗi này được tự động xếp vào Thể loại:Lỗi CS1: PMID.[a]

## Kiểm tra giá trị |ssrn=

Kiểm tra giá trị `|ssrn=`


Tham số `|ssrn=`

là mã định danh của Mạng nghiên cứu khoa học xã hội . SSRN được kiểm tra để đảm bảo rằng nó tham số này chỉ chứa chữ số, không có dấu câu hay dấu cách, có giá trị lớn hơn hoặc bằng 100, nhỏ hơn hoặc bằng 3500000. Các bước kiểm tra sâu hơn không được thực hiện.

Để giải quyết lỗi này, đảm bảo rằng giá trị `|ssrn=`

là chính xác.

Các trang có lỗi này được tự động xếp vào Thể loại:Lỗi CS1: SSRN.[a]

## Kiểm tra giá trị |url=

Kiểm tra giá trị `|url=`


Liên kết ngoài trong bản mẫu chú thích được tạo ra từ hai phần:

*tiêu đề*(`|tiêu đề=`

,`|chương=`

,...); và*URL*(`|url=`

,`|url lưu trữ=`

,`|url chương=`

,...).

Trong đó, *URL* phải có định dạng URI được hỗ trợ. Các URI scheme `http://`

, `https://`

và `//`

được sử dụng phổ biến nhất; `irc://`

, `ircs://`

, `ftp://`

, `news:`

, `mailto:`

và `gopher://`

cũng được hỗ trợ.

URL cũng được kiểm tra để đảm bảo rằng nó chỉ chứa các ký tự Latin và không chứa khoảng trắng. URL có thể là protocol relative (bắt đầu bằng `//`

). Nếu không có khoảng trắng và URL không phải là protocol relative, thì scheme phải tuân thủ RFC 3986.[7]

Tên miền cấp cao nhất và cấp hai được kiểm tra để xác định chúng đúng mẫu. Thông thường, tên miền cấp cao nhất phải có hai chữ cái trở lên; tên miền cấp hai phải có hai chữ cái, chữ số, dấu gạch nối trở lên (ký tự đầu tiên và cuối cùng phải là chữ cái hoặc chữ số). Các tên miền cấp hai đơn ký tự được hỗ trợ:

- tất cả ccTLD (mã quốc gia không được xác thực)
- .org TLD
- một số chữ cái của TLD .com (q, x, z)
- một số chữ cái của TLD .net (i, q)

Tên miền cấp ba và cấp thấp hơn không được kiểm tra. Phần đường dẫn URL không được kiểm tra.

Để giải quyết lỗi này, đảm bảo rằng các tham số URL chứa đường dẫn hợp lệ. Các công cụ trực tuyến hỗ trợ quốc tế hóa các đường dẫn không phải ký tự Latin:

- "IDN Conversion Tool".
*Verisign*. - "IDNA Conversion tool".
*IDNA-converter.com*.

Các trang có lỗi này được tự động xếp vào Thể loại:Lỗi CS1: URL.[a]

## Kiểm tra giá trị |zbl=

Kiểm tra giá trị `|zbl=`


Tham số `|zbl=`

là mã định danh zbl, tham số này sẽ được kiểm tra để đảm bảo nó trông như một mã định danh đúng. Mã định danh `|zbl=`

phải có dạng: nnnn.nnnnn trong đó n là một số tự nhiên từ 0 đến 9, và chỉ có tối đa là ba số 0 đứng đầu trong bộ 4 chữ số (000n.nnnnn). Các bước kiểm tra thêm không được thực hiện.

Để giải quyết lỗi này, hãy đảm bảo rằng giá trị của `|zbl=`

là chính xác.

Các trang có lỗi này được tự động xếp vào Thể loại:Lỗi CS1: Zbl.[a]

## Chú thích sử dụng tham số lỗi thời |<param>

Cite uses deprecated parameter `|<param>`


Qua thời gian, một vài tham số trở nên lỗi thời hoặc không cần thiết. Các biên tập viên được khuyến khích sử dụng các tham số khác thay cho tham số bị phản đối. Các tham số không còn được dùng trong CS1|2 được liệt kê trong bảng sau.

| Tham số lỗi thời | Thay thế bằng |
|---|---|
`|in=`
|
`|ngôn ngữ=`
|

Để giải quyết lỗi này, sử dụng một tham số được khuyến khích để thay thế.

Các trang có lỗi này được tự động xếp vào Thể loại:Lỗi CS1: tham số lỗi thời.[a]

## Chú thích trống

Chú thích trống

Một bản mẫu bị đánh dấu là "Trống" khi không thể nhận dạng được bất kỳ tham số nào. Ví dụ, chú thích này bị đánh dấu "trống" dù nó vẫn chứa thông tin:

`{{chú thích web | http://www.foobar.com | The Foobar Bar}}`


Chú thích này trống vì nó không chứa mã định danh của tham số cần thiết (trong trường hợp này là `|url=`

và `|tiêu đề=`

) để cho `{{chú thích web}}`

biết mà sử dụng thông tin mà chú thích cung cấp.

Chú thích cũng bị đánh dấu là "trống" khi nó có chứa những tham số không thể nhận ra:

`{{cite book |titolo=The Foobar Bar |anno=2015}}`


Chú thích này trống bởi vì những tham số tiếng Ý `|titolo=`

và `|anno=`

không có trong dữ liệu tên tham số của Wikipedia tiếng Việt.

"Chú thích trống" cũng có thể có nghĩa là biên tập viên đã dùng sai bản mẫu cho ý định của mình. Có lẽ biên tập viên đã sử dụng `{{Chú thích}}`

khi đang định sử dụng `{{Cần chú thích}}`

hay `{{trích dẫn}}`

.

Để giải quyết lỗi này, thêm các tham số bị thiếu, dịch các tham số tiếng nước ngoài sang tiếng Việt, hay thay bản mẫu chú thích CS1|2 bằng bản mẫu thích hợp hơn.

Các trang có lỗi này được tự động xếp vào Thể loại:Trang có chú thích trống.[a]

## Liên kết ngoài trong |<param>=

Liên kết ngoài trong `|<param>=`


Lỗi này xảy ra khi bất kỳ tham số tiêu đề nào (`|tiêu đề=`

, `|chương=`

, `|nhà xuất bản=`

, `|work=`

và các biệt danh của nó) chứa liên kết ngoài (url) trong giá trị. Các liên kết ngoài trong các tham số này làm hỏng siêu dữ liệu của chú thích và là nguồn gốc của một loạt các thông báo lỗi khác.

Để giải quyết lỗi này, hãy xóa liên kết ngoài khỏi các tham số tiêu đề và di chuyển nó tới một tham số khác thích hợp hơn:

- với
`|chương=`

, chuyển url tới`|url chương=`

; - với các tham số khác, chuyển url tới
`|url=`

.

Các trang có lỗi này được tự động xếp vào Thể loại:Lỗi CS1: liên kết ngoài.[a]

## |first*n*= missing |last*n*= in Authors/Editors list

`|first`

missing*n*=`|last`

in Authors list*n*=`|first`

missing*n*=`|last`

in Editors list*n*=

*(Lỗi này không hiện tại Wikipedia tiếng Việt, thay vào đó, khi tham số |tên n= không có tham số |họ n= tương ứng, nó sẽ bị ẩn)*


Trong một chú thích, mỗi tham số `|tên `

đều yêu cầu một tham số *n*=`|họ `

tương ứng. Danh sách tác giả và biên tập viên sẽ được kiểm tra để ghép họ/tên cho thích hợp; nếu có một cặp họ/tên không thích hợp, CS1|2 sẽ phát thông báo lỗi cho cặp đầu tiên nó phát hiện; nếu có nhiều cặp họ/tên bị lỗi trong chú thích, những cặp sau sẽ không được phát hiện.
*n*=

Ngược lại, tham số `|họ `

không yêu cầu bắt buộc phải có một tham số *n*=`|tên `

tương ứng.
*n*=

Để giải quyết lỗi này, hãy đảm bảo rằng mỗi `|tên `

đều có một *n*=`|họ `

tương ứng.
*n*=

Các trang có lỗi này được tự động xếp vào Thể loại:Lỗi CS1: thiếu tác giả hoặc biên tập viên.[a]

## |format= cần |url=

`|format=`

cần`|url=`

(thông báo lỗi được mặc định ẩn)`|...-format=`

cần`|...-url=`

(thông báo lỗi được mặc định ẩn)

Lỗi xảy ra khi chú thích sử dụng `|format=`

hoặc `|...-format=`

mà không cung cấp url tương ứng cho tham số `|url=`

hoặc `|...-url=`

. Các tham số `|format=`

và `|...-format=`

được sử dụng để xác định định dạng tệp tài liệu (ví dụ: PDF, DOC, XLS,...) mà chú thích sử dụng. Trong một số trường hợp, biên tập viên có thể sử dụng tham số `|type=`

để chỉ định loại tài liệu (ví dụ: bìa cứng, bìa mềm, tờ rơi,...).

Danh sách các tham số `|...-format=`

:

`|archive-format=`

,`|chapter-format=`

,`|conference-format=`

,`|contribution-format=`

,`|event-format=`

,`|lay-format=`

,`|section-format=`

,`|transcript-format=`


Kể từ ngày 29 tháng 11 năm 2014, tham số `|chapter-format=`

được thêm mới vào. Một vài chú thích cũ có thể cần chỉnh sửa một chút (`|url=`

và `|format=`

) cho phù hợp.

Để giải quyết lỗi này,

- xóa bỏ
`|format=`

hoặc`|chapter-format=`

; hoặc - thêm giá trị cho tham số
`|url=`

hoặc`|chapter-url=`

; hoặc - thay tham số
`|format=`

thành`|type=`

(hoặc thành`|chapter-format=`

nếu sử dụng`|chapter-url=`

mà không có`|url=`

).

Các trang có lỗi này được tự động xếp vào Thể loại:Trang có chú thích có định dạng mà không có URL.[a]

## Invalid <param>=<value>

Invalid `|<param>=<value>`


Để hoạt động đúng, một số tham số được giới hạn trong một tập hợp giá trị nhất định. Thông báo lỗi này xuất hiện khi một tham số đã không được gán một giá trị trong tập hợp giá trị của nó.

| tham số | giá trị được chấp nhận | chú thích |
|---|---|---|
`|dead-url=` |
`no` , `true` , `y` , `yes` , `unfit` , `usurped`
|
|
`|df=` |
`dmy` , `dmy-all` , `mdy` , `mdy-all` , `ymd` , `ymd-all`
|
tham số không hoạt động ở vi.wiki |
`|ignore-isbn-error=` |
`true` , `y` , `yes`
|
|
`|last-author-amp=`
|
||
`|mode=` |
`cs1` , `cs2`
|
|
`|name-list-style=` |
`vanc`
|
|
`|nopp=` |
`true` , `y` , `yes`
|
|
`|no-tracking=`
|
||
`|registration=`
|
||
`|subscription=`
|
||
`|url-access=` |
`subscription` , `registration` , `limited`
|
|
`|bibcode-access=` |
`free`
|
|
`|doi-access=`
|
||
`|hdl-access=`
|
||
`|jstor-access=`
|
||
`|ol-access=`
|
||
`|osti-access=`
|

Để giải quyết lỗi này, hãy sử dụng một giá trị thích hợp

Các trang có lỗi này được tự động xếp vào Thể loại:Lỗi CS1: giá trị tham số không hợp lệ.[a]

## Khuyết |last*n*= trong danh sách tác giả/biên tập

- Missing
`|last`

in Authors list*n*= - Missing
`|last`

in Editors list*n*=

Tất cả các tác giả và biên tập viên được liệt kê trong chú thích đều sẽ được hiển thị, cho nên Mô đun không được thiết kế cứng sẽ có bao nhiêu tham số tác giả; các bản mẫu chú thích yêu cầu n trong `|tác giả `

tăng thêm một đơn vị khi có thêm một tác giả được thêm vào. Thông báo lỗi hiển thị khi có một đứt đoạn trong dãy số, ví dụ: danh sách có *n*=`|tác giả 1=`

và `|tác giả 3=`

nhưng lại khuyết `|tác giả 2=`

.

Kiểm tra sẽ không phát hiện ra đứt đoạn lớn hơn 1, nghĩa là khi `|tác giả `

và *n+1*=`|tác giả `

đều không có, thì danh sách sẽ kết thúc tại *n+2*=`|tác giả `

.
*n*=

Thông báo hiển thị dưới dạng tốc ký: `|last`

có thể là bất kỳ biệt danh hợp lệ nào của *n*=`|tác giả=`

trong danh sách tác giả.

Để giải quyết lỗi này, đảm bảo rằng tham số `|tác giả `

được tăng đúng.
*n*=

Các trang có lỗi này được tự động xếp vào Thể loại:Lỗi CS1: thiếu tác giả hoặc biên tập viên.[a]

## |tiêu đề= trống hay bị thiếu

### URL không có tiêu đề

`|<param>=`

trống hay bị thiếu

Lỗi này xảy ra khi chú thích có URL nhưng lại không được nhập tiêu đề tương ứng. Lỗi này cũng có thể xảy ra do `|tiêu đề=`

không thể liên kết được với `|url=`

vì bản mẫu chú thích đồng thời được khai báo `|lk tiêu đề=`

gây xung đột.

| Tham số URL | Tham số tiêu đề |
|---|---|
`|url lưu trữ=`
|
`|tiêu đề=`
|
`|url chươngl=`
|
`|chương=` , `|mục=`
|
`|url hội nghị=` , `|url sự kiện=`
|
`|hội nghị=` , `|sự kiện=`
|
`|lk bản sao=`
|
`|bản sao=`
|
`|url=`
|
`|tiêu đề=`
|

Một trường hợp đặc biệt: nếu `|pmc=`

có giá trị và `|url=`

trống, thì `|tiêu đề=`

sẽ liên kết tới cùng một URL với PMC.

Để giải quyết lỗi này, cung cấp một tiêu đề thích hợp cho tham số tiêu đề tương ứng. Nếu có xung đột giữa `|url=`

và `|lk tiêu đề=`

, bạn cần phải chọn một cái để giữ lại. Cân nhắc việc chuyển `|url=`

hoặc `|lk tiêu đề=`

sang một tham số phù hợp hơn.

Các trang có lỗi này được tự động xếp vào Thể loại:Trang có URL không tên trong chú thích.[a]

### Chú thích không có tiêu đề

`|tiêu đề=`

trống hay bị thiếu

Lỗi này xảy ra khi bản mẫu chú thích bỏ trống tất cả các tham số `|tiêu đề=`

, `|dịch tiêu đề=`

, `|tiêu đề chữ khác=`

. Phải có ít nhất một trong số các tiêu đề được khai báo trong bản mẫu chú thích.

`{{Chú thích phần chương trình}}`

sẽ hiển thị lỗi này nếu `|series=`

bị bỏ trống (ngay cả khi đã có `|tiêu đề=`

).

Để giải quyết lỗi này, cung cấp giá trị cho `|tiêu đề=`

, `|dịch tiêu đề=`

và/hoặc `|tiêu đề chữ khác=`

hoặc thay thế bản mẫu chú thích bằng một bản mẫu khác thích hợp hơn.

Các trang có lỗi này được tự động xếp vào Thể loại:Lỗi CS1: thiếu tiêu đề.[a]

## |url= trống hay bị thiếu

`|url= trống hay bị thiếu`

(thông báo lỗi được mặc định ẩn)
Thông báo lỗi này được hiện bởi các bản mẫu `{{chú thích web}}`

, , và `{{cite podcast}}`

`{{Chú thích danh sách thư}}`

khi các tham số `|url=`

và `|archive-url=`

đều thiếu, trống hoặc không chính xác. Lưu ý rằng `|website=`

hay `|work=`

là tên của trang web chứ không phải là url.

Để giải quyết lỗi này, hãy bổ sung giá trị cho `|url=`

, hoặc sử dụng một bản mẫu khác thích hợp hơn như {{chú thích sách}}, {{chú thích tạp chí}} hoặc các bản mẫu chú thích khác.

Các trang có lỗi này được tự động xếp vào Thể loại:Trang có chú thích Web thiếu URL.[a]

## Đã định rõ hơn một tham số trong |<param1>=, |<param2>=, và |<param3>=

`|<param1>=`

, `|<param2>=`

, và `|<param3>=`

specified
Lỗi này xảy ra khi chú thích sử dụng nhiều hơn một tham số đồng nghĩa. Ví dụ, `|tác giả=`

, `|họ=`

và `|họ 1=`

là các tham số đồng nghĩa, chúng sử dụng chung một biến gốc tại Mô đun, do đó không nên sử dụng chung các tham số này trong một chú thích.

Để giải quyết lỗi này, loại bỏ hoặc thay đổi các tham số đồng nghĩa.

- More than one of author-name-list parameters specified
- More than one of editor-name-list parameters specified

Lỗi này xảy ra khi chú thích sử dụng đồng thời nhiều kiểu danh sách tên tác giả hoặc biên tập viên khác nhau. Có ba kiểu danh sách không tương thích với nhau:

`|tác giả`

,*n*=`|họ`

/*n*=`|tên`

*n*=`|vauthors=`

`|các tác giả=`


tương tự, có ba kiểu danh sách biên tập viên không tương thích:

`|biên tập=`

,`|họ biên tập`

/*n*=`|tên biên tập`

*n*=`|veditors=`

`|các biên tập viên=`


Để giải quyết lỗi này, chọn một kiểu danh sách tên. Sử dụng kiểu danh sách đã chọn cho cả danh sách tác giả và biên tập.

Các trang có lỗi này được tự động xếp vào Thể loại:Trang có tham số chú thích dư.[a]

## Đã bỏ qua văn bản “xxx”

Không giống như nhiều bản mẫu Wikipedia khác, bản mẫu CS1|2 không sử dụng các tham số không có tên. Khi văn bản giữa hai thanh dọc (|) không chứa dấu bằng (=), CS1|2 sẽ bỏ qua văn bản và báo lỗi. Điều này đúng ngay cả khi văn bản là tên của một tham số hợp lệ.

Lỗi này cũng có thể xảy ra khi các thanh dọc (|) chứa trong url hoặc tiêu đề. Khi thanh dọc (|) xuất hiện trong url, hãy thay thế chúng bằng `%7c`

. Khi các thanh dọc (|) xuất hiện trong các tham số khác không phải url, hãy thay thế chúng bằng `|`

hoặc `{{!}}`

.

Để giải quyết lỗi này,

- xóa văn bản không hợp lệ;
- thêm dấu bằng (=);
- thêm tham số thích hợp ứng với mục đích sử dụng của bạn;
- mã hóa thanh dọc trong url và tiêu đề.

Các trang có lỗi này được tự động xếp vào Thể loại:Trang có tham số chú thích không tên.[a]

## |dịch <param>= cần |<param>=

`|dịch tiêu đề=`

cần`|tiêu đề=`

`|dịch chương=`

cần`|chương=`


Các bản mẫu chú thích hiện lỗi này khi có tiêu đề `|dịch tiêu đề=`

hay tên chương `|dịch chương=`

đã được dịch sang tiếng Việt nhưng lại không có tiêu đề `|tiêu đề=`

hay tên chương `|chương=`

trong ngôn ngữ gốc.

Để giải quyết lỗi này, bổ sung tiêu đề `|tiêu đề=`

hoặc tên chương `|chương=`

trong ngôn ngữ gốc. Xem xét việc thêm tham số `|ngôn ngữ=`

nếu nó chưa có trong chú thích.

Các trang có lỗi này được tự động xếp vào Thể loại:Trang có chú thích thiếu tên nguyên ngữ.[a]

## Đã bỏ qua tham số không rõ |xxxx=

- Đã bỏ qua tham số không rõ
`|xxxx=`

- Đã bỏ qua tham số không rõ
`|xxxx=`

(`|yyyy=`

suggested)

Bản mẫu chú thích CS1|2 sẽ báo lỗi này khi phần tên của cặp tham số `|tên=giá trị`

được nhận dạng là một tên không hợp lệ. Thông thường, lỗi xảy ra từ lỗi chính tả hoặc viết hoa.

Trong các chú thích kiểu cũ, một tham số có tên không hợp lệ đơn giản là bị bỏ qua và ẩn đi. Công cụ CS1|2 lại nói không với điều này; mục đích của chú thích là xác định đúng nguồn gốc; chứ không phải là một kho lưu trữ các ghi chú và thông tin phụ trợ.

Các tham số của CS1|2 đều là chữ thường; CS1|2 sẽ báo lỗi khi tên tham số nào đó chứa chữ cái in hoa (Xxxx, xxXx, XXXX). Ngoại lệ là các tham số định danh, như `|isbn=`

, `|pmc=`

, `|doi=`

,... có thể sử dụng chữ thường hoặc chữ hoa, nhưng không được sử dụng hỗn hợp (`|isbn=`

hoặc `|ISBN=`

được chấp nhận, còn `|Isbn=`

thì không). Đối với các lỗi chính tả phổ biến, ví dụ như `|pubisher=`

thay vì `|publisher=`

, CS1|2 sẽ đề xuất một tên tham số hợp lệ.

Để giải quyết lỗi này, thay thế tên tham số sai bằng tên chính xác, có thể sử dụng tên được đề xuất. Đảm bảo rằng tên tham số được viết đúng chính tả và không có ký tự nào ngoại trừ khoảng trắng giữa tên tham số và thanh dọc (|) hoặc dấu bằng (=). Có thể tìm thấy danh sách các tham số hợp lệ tại trang mô tả của bản mẫu đang sử dụng, chẳng hạn `{{chú thích web}}`

, `{{chú thích sách}}`

, `{{chú thích tạp chí}}`

,... Hãy xem xét việc chuyển thông tin trong tham số không hợp lệ sang một tham số thích hợp, hoặc chuyển nó đến trang thảo luận của bài viết để lưu giữ.

Các trang có lỗi này được tự động xếp vào Thể loại:Trang có tham số chú thích không rõ.[a]

## Đã bỏ qua tham số không rõ |dead-url=

- Đã bỏ qua tham số không rõ
`|dead-url=`


Tham số `|dead-url=yes`

(hoặc `|dead-url=no`

) trước đây được sử dụng tại Wikipedia tiếng Việt để thay thế đường link gốc đã hỏng bằng đường link lưu trữ. Hiện tại, tham số này không được sử dụng, thay vào đó, tại đây sử dụng tham số `|url-status=dead`

.

Để giải quyết lỗi này, hãy thay thế `|dead-url=yes`

bằng `|url-status=dead`

, `|dead-url=no`

bằng `|url-status=live`

.

Các trang có lỗi này được tự động xếp vào Thể loại:Trang có tham số chú thích không rõ.[a]

## Đã bỏ qua tham số không rõ |df=

- Đã bỏ qua tham số không rõ
`|df=`


Tham số `|df=`

thường được sử dụng tại Wikipedia tiếng Anh để định dạng cách hiển thị ngày tháng. Tại Wikipedia tiếng Việt, tham số này không được sử dụng và cũng không có tham số thay thế.

Để giải quyết lỗi này, hãy xóa tham số `|df=`

.

Các trang có lỗi này được tự động xếp vào Thể loại:Trang có tham số chú thích không rõ.[a]

## Đã bỏ qua tham số không rõ |contributor=

- Đã bỏ qua tham số không rõ
`|contributor=`


Tham số `|contributor=`

là một tham số hiếm khi được sử dụng tại Wikipedia tiếng Anh để xác định tác giả của một đóng góp, thường là lời bạt, giới thiệu, lời nói đầu... cho một tác giả chính khác. Tại Wikipedia tiếng Việt, tham số này không được sử dụng; thay vào đó, hãy sử dụng tham số `|người khác=`

.

Để giải quyết lỗi này, hãy thay tham số `|contributor=`

bằng `|người khác=`

.

Các trang có lỗi này được tự động xếp vào Thể loại:Trang có tham số chú thích không rõ.[a]

## URL chứa liên kết wiki

Các liên kết trong chú thích có thể được tạo ra theo hai cách, nhập liên kết ngoài vào `|url=`

, `|url chương=`

,... hoặc tạo liên kết wiki trong `|tiêu đề=`

, `|chương=`

,... Khi liên kết ngoài và liên kết wiki cùng được sử dụng, liên kết wiki sẽ bị bỏ qua và thông báo lỗi.

Một số bản mẫu cũng sẽ gây lỗi khi được sử dụng trong các tham số tiêu đề (ví dụ: các bản mẫu `{{lang}}`

tạo ra thể loại). Các bản mẫu được sử dụng trong các tham số url cũng có thể làm hỏng COinS metadata của chú thích. Hãy tránh sử dụng bản mẫu trong các tham số này, trừ khi bạn biết rõ kết quả sẽ xảy ra.

Lỗi này cũng có thể xảy ra trong các bản mẫu dựa trên mã định danh (`{{cite doi}}`

,...). Khi đó, thông báo lỗi được hiển thị trong bài viết nhưng lỗi thực sự thì nằm trong bản mẫu chú thích.

Để giải quyết lỗi này, xóa liên kết wiki trong các tham số tiêu đề hoặc xóa các url liên kết ngoài. Nếu bạn muốn hiển thị song song cả hai loại liên kết, hãy di chuyển liên kết wiki ra ngoài bản mẫu chú thích, nhưng vẫn đặt chúng trong cặp thẻ `<ref>...</ref>`

của chú thích đó.

Nếu bạn tin rằng bản mẫu chú thích hoạt động sai, hãy liên hệ bảo quản viên để nhờ nâng cấp Mô đun chú thích.

Các trang có lỗi này được tự động xếp vào Thể loại:Lỗi CS1: URL chứa liên kết wiki.[a]

## Lỗi văn phong Vancouver

Lỗi này hiển thị trong các chú thích sử dụng tham số `|name-list-style=vanc`

. Văn phong Vancouver hạn chế tên tác giả hoặc biên tập viên trong bảng chữ cái Latin. Trong kiểm tra này, Mô đun:Citation/CS1 định nghĩa bảng chữ cái Latin là các chữ cái được xác định trong bộ ký tự Unicode Latin:

- C0 Controls and Basic Latin
[8](0041–005A, 0061–007A) - C1 Controls and Latin-1 Supplement
[9](00C0–00D6, 00D8–00F6, 00F8–00FF) - Latin Extended-A
[10](0100–017F) - Latin Extended-B
[11](0180–01BF, 01C4–024F)

Lỗi này cũng hiển thị khi một tác giả hoặc tổ chức được liệt kê trong `|vauthors=`

không sử dụng dấu phân cách thích hợp. Các tác giả là tổ chức nên được liệt kê theo cách này:

`|vauthors=First Surname FM, Surname AB,`

((Corporate or institutional Author)), Lastsurname XY

Mặc dù thường chính xác, nhưng thỉnh thoảng, tên tác giả bị PMID liệt kê lỗi khi viết thường trợ từ họ quý tộc (phương Tây). Ví dụ, PMID 17726700 đã viết tên của Magnus von Knebel Doeberitz là Doeberitz Mv; không đúng. Tên của tác giả này nên được viết là `|vauthors=von Knebel Doeberitz M`

.[12]

Một số dấu câu cũng sẽ bị báo lỗi. Ví dụ, Unicode U+2019, dấu nháy đơn phải, gây ra lỗi vì nó không thuộc bộ ký tự Latin đã được xác định ở trên: `|vauthors=Van’t Veer M`

. Hãy thay thế ký tự này bằng dấu nháy đơn: `|vauthors=Van't Veer M`

.

Để giải quyết lỗi này, Latin hóa tên tác giả và biên tập viên.[13] Latin hóa có thể dẫn đến việc một chữ cái bị phiên thành hai chữ cái, ví dụ, chữ cái Hy Lạp 'Θ' sẽ bị Latin hóa thành 'Th'.[14] Khi đó, Mô đun:Citation/CS1 không thể biết chữ cái này là một lỗi chính tả hay một ký tự Latin hợp lệ nên sẽ thông báo lỗi Vancouver. Nếu bạn xác định rằng các ký tự này là chính xác và không bị lỗi chính tả, hãy xử lý tên đó như thể đó là tên tổ chức bằng cách đặt nó trong cặp ngoặc đơn ×2: `|vauthors=..., Tatarinov IuS, ...`

→ `|vauthors=..., ((Tatarinov IuS)), ...`

.

Tương tự với tên tiếng Trung. Ví dụ, tên tác giả 'Wang Hsien-yu' được viết là 'Wang Hy', nó sẽ gây ra lỗi Vancouver. Khi đó hãy xác minh rằng đây là một tên hợp lệ và bọc chúng trong cặp ngoặc đơn ×2.

Các trang có lỗi này được tự động xếp vào Thể loại:Lỗi CS1: văn phong Vancouver.[a]

## <char> character in |<param>= at position *n*

`|<param>=`

at position *n*

Lỗi hiển thị khi giá trị tham số trong chú thích chứa các ký tự vô hình được gọi là control character; *n* trong thông báo lỗi là vị trí của ký tự. Mô đun có thể phát hiện các ký tự sau đây:

- replacement character, U+FFFD
- hair space, U+200A
- zero width space, U+200B
- zero width joiner, U+200D
- soft hyphen, U+00AD
- horizontal tab, U+0009 (HT)
- line feed, U+0010 (LF)
- carriage return, U+0013 (CR)
- delete character, U+007F (DEL)
- C0 control, U+0000–U+001F (NULL–US)
- C1 control, U+0080–U+009F (XXX–APC)

Để giải quyết lỗi này, hãy xóa ký tự được Mô đun xác định. Vì các ký tự này vô hình, thông báo lỗi sẽ xác định vị trí của nó từ trái qua phải, không tính khoảng trắng giữa dấu bằng (=) và giá trị tham số.

<name> stripmarker in `|<param>=`

at position *n*

Stripmarker là các chuỗi ký tự đặc biệt mà MediaWiki chèn dưới dạng place-holder cho các thẻ giống xml nhất định. Những thẻ này gồm có: `<gallery>...</gallery>`

, `<math>...</math>`

, `<nowiki>...</nowiki>`

, `<pre>...</pre>`

, và `<ref>...</ref>`

. Mô đun bỏ qua thẻ math và nowiki.

Để giải quyết lỗi này, hãy xóa hoặc thay thế những thẻ đã xác định. Thông báo lỗi xác định vị trí Stripmarker từ trái qua phải, không tính khoảng trắng giữa dấu bằng (=) và giá trị tham số.

Các trang có lỗi này được tự động xếp vào Thể loại:Lỗi CS1: ký tự ẩn.[a]

## |<param>-truy cập= cần |<param>=

`|<param>-access=`

cần `|<param>=`

Lỗi xuất hiện khi tham số khai báo liên kết đã được nhập nhưng tham số bắt buộc tương ứng lại bị bỏ trống. Tham số có thể là một trong

| tham số đã nhập | tham số bắt buộc còn thiếu |
|---|---|
`|url-access=` |
`|url=`
|
`|bibcode-access=` |
`|bibcode=`
|
`|doi-access=` |
`|doi=`
|
`|hdl-access=` |
`|hdl=`
|
`|jstor-access=` |
`|jsor=`
|
`|ol-access=` |
`|ol=`
|
`|osti-access=` |
`|osti=`
|

Để giải quyết lỗi này, cung cấp giá trị cho tham số yêu cầu hoặc xóa tham số xx-truy cập.

Các trang có lỗi này được tự động xếp vào Thể loại:Lỗi CS1: param-access.[a]

## Không cho phép mã đánh dấu trong: |<param>=

`|<param>=`

Mã Wiki nghiêng (`''`

) hoặc đậm (`'''`

) không được phép trong tham số publisher và periodical. Cụ thể những tham số này bao gồm:

`|publisher=`

`|journal=`

`|magazine=`

`|newspaper=`

`|periodical=`

`|website=`

`|work=`


Để giải quyết lỗi này, hãy xóa mã wiki khỏi các tham số trên và đảm bảo rằng bản mẫu đang sử dụng các tham số chính xác; khi trích dẫn một tờ báo, hãy sử dụng `|newspaper=`

cho tên của tờ báo, không dùng `|publisher=`

,....

Trang có chú thích bị lỗi này được đưa vào Thể loại:Lỗi CS1: mã đánh dấu.[a]

## |script-<param>= không hợp lệ: <type>

`<type>`

Nhiều kiểu tham số `|script-<`

có quy định hình thức phù hợp. Khi lỗi được phát hiện, thông báo lỗi xác định ngắn gọn loại lỗi:
`param`>=

- missing title part – tham số
`|script-<`

có tiền tố mã ngôn ngữ nhưng trống`param`>= - missing prefix – tham số
`|script-<`

có văn bản nhưng thiếu tiền tố mã ngôn ngữ bắt buộc; tiền tố có dạng`param`>=`xx:`

hoặc`xxx:`

với`xx`

hoặc`xxx`

là một mã ngôn ngữ hợp lệ theo ISO 639-1 hoặc ISO 639-3 được sử dụng bởi CS1|2 như một ngôn ngữ sử dụng hệ thống chữ viết không phải chữ Latinh; dấu hai chấm (`:`

) là bắt buộc - unknown language code – tham số
`|script-<`

có mã ngôn ngữ (có thể hợp lệ) mà CS1|2 không nhận ra là ngôn ngữ sử dụng hệ thống chữ viết không phải chữ Latinh`param`>=

Các trang có lỗi này sẽ tự động được đưa vào Thể loại:Lỗi CS1: tham số hệ thống viết.[a]

## |số tác giả-<names>=<value> không hợp lệ


Các thông báo lỗi này xuất hiện khi Module:Citation/CS1 xác định các trích dẫn sử dụng một hoặc nhiều tham số `|số tác giả-<names>=`

với một chỉ định `<value>`

không hợp lệ. Chỉ định `<value>`

không hợp lệ là một số lớn hơn hoặc bằng số `<names>`

trong danh sách tên được liên kết hoặc đó là văn bản không phải số mà Module:Citation/CS1 không thể nhận dạng là một dạng của từ khóa `etal`

.

Để giải quyết lỗi này, hãy thực hiện một trong các thao tác sau:

- Xóa tham số
`|số tác giả-<names>=`

khỏi chú thích (vì "et al." không phù hợp trong chú thích) - Thay đổi
`<value>`

của tham số`|số tác giả-<names>=`

sao cho nó ít hơn số`<names>`

trong danh sách tên (do đó cắt bớt danh sách được hiển thị thành số) - Thay đổi
`<value>`

của tham số`|số tác giả-<names>=`

đến`etal`

, điều này sẽ khiến "et al" hiển thị sau`<name>`

.

Các trang có lỗi này sẽ tự động được đưa vào Thể loại:Lỗi CS1: số tên hiển thị.[a]

## Chú thích có tiêu đề chung

Các bài viết được liệt kê trong thể loại này khi Module:Citation/CS1 xác định bản mẫu có tham số `|title=`

sử dụng tiêu đề giữ chỗ. Những tiêu đề như vậy có thể được cung cấp bởi bot hoặc các công cụ khác không thể xác định được tiêu đề chính xác của nguồn. Các trang trong thể loại này chỉ nên được thêm vào theo Module:Citation/CS1.

CS1|2 duy trì một danh sách ngắn các 'tiêu đề' thường không phải là tiêu đề của nguồn được trích dẫn. Một số ví dụ:

- Wayback machine
- Trang web này là để bán
- Bạn là một robot?

Nếu bạn biết về các tiêu đề giữ chỗ phổ biến khác, vui lòng báo cáo chúng, để thêm vào danh sách.

Để giải quyết lỗi này, hãy thay thế tiêu đề giữ chỗ bằng tiêu đề thực của nguồn.

Các trang có lỗi này sẽ tự động được đưa vào Thể loại:Lỗi CS1: tiêu đề chung.[a]



## Ghi chú

- ^
**a****b****c****d****e****f****g****h****i****j****k****l****m****n****o****p****q****r****s****t****u****v****w****x****y****z****aa****ab****ac****ad****ae****af****ag****ah****ai****aj****ak****al****am****an****ao****ap****aq****ar****as****at****au****av****aw****ax****ay****az****ba**Các trang thảo luận sẽ không được liệt kê vào thể loại lỗi.**bb** **^**Chú thích này hiện chưa sử dụng Mô đun, nhưng lỗi này cũng tương tự ở các chú thích sử dụng mô đun**^**ngày tháng viết bằng tiếng Anh vẫn được chấp nhận tại Wikipedia tiếng Việt, những ngôn ngữ khác không được chấp nhận

## Tham khảo

- ^
**a**"archive.org website".**b** - ^
**a**"webcitation.org website".**b** **^**"Understanding the arXiv identifier".*Cornell University Library*. Truy cập ngày 20 tháng 8 năm 2014.**^**"1.2.3 - Bibliographic Identifiers".*The SAO/NASA Astrophysics Data System*.**^**"The LCCN Namespace".*Network Development and MARC Standards Office*. Library of Congress. tháng 11 năm 2003.**^**"Netnews Article Format".*Internet Engineering Task Force*. tháng 11 năm 2009. 3.1.3. RFC 5536.**^**"Scheme".*Uniform Resource Identifier (URI): Generic Syntax*. Internet Engineering Task Force. tháng 1 năm 2005. RFC 3986.**^**"C0 Controls and Basic Latin" (PDF).*Unicode*. Truy cập ngày 19 tháng 4 năm 2015.**^**"C1 Controls and Latin-1 Supplement" (PDF).*Unicode*. Truy cập ngày 19 tháng 4 năm 2015.**^**"Latin Extended-A" (PDF).*Unicode*. Truy cập ngày 19 tháng 4 năm 2015.**^**"Latin Extended-B" (PDF).*Unicode*. Truy cập ngày 19 tháng 4 năm 2015.**^**"Other surname rules".*National Center for Biotechnology Information*.**^**Patrias K (2007). "Names in non-roman alphabets or character-based languages". Trong Wendling D (biên tập).*Citing Medicine: The NLM Style Guide for Authors, Editors, and Publishers [Internet]*(ấn bản thứ 2). Bethesda: National Library of Medicine.**^**"Greek" (PDF).*Library of Congress*.