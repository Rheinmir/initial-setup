Hơn 100 giờ vibe code, mình đã biết cách tạo website không “xúc phạm người nhìn” 

Kể từ khi AI bùng nổ, mình nhìn thấy rác ở khắp mọi nơi. Đặc biệt là đối với các website. 

Gradient xanh tím, Icon tùm lum, các nút bấm với hiệu ứng glowing chói hơn ánh mặt trời, các animation xuất hiện không cần thiết. 

Buồn cười là kể cả các website hứa hẹn là sẽ giúp bạn design đẹp hơn với AI cũng được thiết kế xấu ná thở. 

Nhưng có thực sự phải như vậy? Kể cả vibe coding cũng có thể tạo ra những website đẹp, vì về căn bản AI cũng chỉ là công cụ. Nếu vào tay người biết cách thiết kế, nó vẫn có thể tạo ra những trang web làm mãn nhãn người xem. 

Cá nhân mình cũng dùng AI để tạo ra web portfolio và thậm chí là design web bán được cả chục triệu. Mình vẫn nhớ cảm giác tự hào khi mình gửi web portfolio cho bạn designer mình quen, và bạn ấy chỉ nhắn đúng 4 chữ. “Damn, So f.. nice”

Bài viết này, mình sẽ chia sẻ các bạn một số phương pháp mình đã áp dụng để có thiết kế đẹp hơn với AI. 

1. Mình dùng model nào?

Sau khi đã thử nghiệm qua 3 phổ biến bậc nhất là Gemini 3.1 pro, Opus 4.8, và Gpt 5.5, model mình thấy ấn tượng nhất về UI là …Gemini 3.1 pro. Ít nhất nếu so về khả năng one shot (1 prompt ra luôn kết quả). 

Vì model của Google được huấn luyện rất kỹ về mặt hình ảnh, nên mình thấy gemini có thể tạo được các pattern khá phức tạp mà mình thấy các model khác không làm được, hoặc phải prompt thật kỹ thì mới ra. 

Thú thực mình chưa thử opus 4.8 quá nhiều để chắc chắn là gemini 3.1 pro có vượt trội hơn nó về design hay không, nhưng mình chắc chắn về thẩm mỹ gemini 3.1 pro tốt hơn gpt 5.5. 

Thường bây giờ workflow thiết kế của mình sẽ là tạo brief thiết kế (mình sẽ nói kỹ hơn ở mục khác) và đưa vào gemini để tạo khoảng 5 thiết kế khác nhau. Chọn thiết kế mình thích và sau đó tải code của thiết kế đó về để chỉnh tiếp bằng Codex. 

Lý do mình không dùng tiếp Gemini mà chuyển qua Codex là vì…. mình không có subscription của Antigravity hay của Google AI. Mà mấy lần trước mình dùng thì thấy Gemini tạo ra các bản thiết kế đầu tiên khá đẹp, nhưng nếu muốn tinh chỉnh nhiều hơn thì sẽ thấy nó không giỏi trong việc nghe theo hướng dẫn cho lắm. 

2. Front-end design skills

Skill đơn giản là bản hướng dẫn để AI đọc trước khi làm tác vụ nào đó. Front-end design skills tập hợp những nguyên tắc để AI đọc trước khi tạo ra thiết kế. 

Một số nguyên tắc ở trong Front-end design skills:

- Hiểu được nguyên tắc sản phẩm trước khi tạo thiết kế

- Theo một hướng thiết kế độc đáo và riêng biệt (Bold and Extreme) thay vì một hướng chung chung

- Chọn những font chữ đẹp và độc đáo, tránh những font như Arial

- Tránh purple gradient 😎

Và nhiều nguyên tắc khác. 

Đơn giản thế thôi nhưng nó cũng giúp tăng khả năng thiết kế của coding agent lên đáng kể. 

Ngoài ra, bạn hoàn toàn có thể điều chỉnh front-end design skills theo ý bạn. Trong front-end design skills có bảo rằng dùng minimalism (tối giản) hay maximalism (tối đa) đều được, miễn là có chủ đích trong việc dùng nó. Mình thì thích minimalism hơn nên mình sửa skills lại, bảo là dùng minimalism trong mọi trường hợp. 

Để sửa skills thì các bạn chỉ cần prompt cho coding agents hoặc sửa trực tiếp trong file [skill.md](http://skill.md). 

Nếu muốn sử dụng front-end design skill, bạn chỉ cần tìm kiếm skill này trên skills. sh và tải về theo hướng dẫn là được. Sau này coding agents sẽ tự động dùng front-end design skills mỗi lần có tác vụ thiết kế front-end. 

3. Một số nguyên tắc khác. 

3.1 THỰC SỰ tối giản

Nhìn chung, mình luôn thích thiết kế tối giản hơn thiết kế nhiều màu sắc, vì nó mang lại một vẻ sang trọng, hiện đại và khiến người dùng không rối mắt. 

Mình thường theo quy luật số ba: Một thiết kế không có quá 3 màu chủ đạo, không có quá 3 font chữ khác nhau (thường mình chỉ dùng 2 hoặc 1 font), và không bắt người dùng phải xem quá 3 cụm thông tin cùng một lúc. 

Tuy nhiên, không phải lúc nào câu “less is more” cũng đúng. Nhiều khi một số website xoá quá nhiều chi tiết, không có slogan cũng chả có logo, nên người dùng không thực sự biết nó về cái gì. 

Nên tối giản ở đây, đối với mình không phải là có ít chi tiết, mà có vừa đủ các chi tiết cần thiết, không thừa không thiếu. 

Ví dụ, trong video review website của Startup trong Y Combinator (vườn ươm khởi nghiệp nổi tiếng bậc nhất thế giới), Ryo Lu (Head of Design của Cursor) và Aaron Epstein (partner tại YC) nhận xét website của một công ty tạo video cho các thương hiệu. 

Website nhìn rất đơn giản, chỉ có đúng một dòng chữ “Create detailed brand videos with AI”, rồi ở dưới là ví dụ video thương hiệu này làm ra. Vấn để của trang này là nó không cung cấp thêm bất kỳ thông tin nào cho thấy sự khác biệt của nó với các thương hiệu khác. Tạo video là video gì, UGC, hay quảng cáo ngắn, hay dạng nào khác? Rồi dùng sản phẩm của thương hiệu này thì khác gì so với những công cụ tạo video khác như Veo, Pixverse? 

Tối giản, không có nghĩa là có ít chi tiết. 

Ngoài ra, bây giờ, vì có AI nên làm hiệu ứng rất dễ. Hầu như website nào cũng có rất nhiều animation, nhiều chi tiết trông rất ấn tượng. 

Nhưng, câu hỏi quan trọng là: Thêm các chi tiết đó vào để làm gì?

 Nhiều thiết kế thêm animation vào chỉ để nhìn cho đẹp, nhưng thực tế thì nó rất loạn mắt và khiến khách hàng sao nhãng khỏi nút bấm mà ta thực sự muốn họ chú ý. 

Câu chuyện bạn muốn kể thông qua website là gì? Hành động nào các bạn muốn người dùng làm?

Xoá tất cả những chi tiết không trực tiếp trả lời hai câu hỏi này. 

3.2 Đừng hy vọng one shot. 

Rất khó để chỉ prompt một lần là các bạn sẽ có thiết kế đẹp. 

Công thức tạo ra thiết kế buồn ói: Prompt một lần, không cho nó brief, và bê nguyên thiết kế đầu tiên từ AI cho người dùng sử dụng. 

Để có thiết kế đẹp, các bạn nên chuẩn bị tinh thần prompt cho Ai nhiều lần. Điều này đơn giản nhưng nhiều bạn quên, vì lười hoặc vì thiếu credit

Thường thì AI vẫn sẽ có những lỗi nhỏ, ví dụ như chữ lệch ra khỏi nút bấm, dùng các icon chung chung, chữ không thẳng hàng… 

Thực chất, những chi tiết này có thể không quá nhiều người để ý, nhưng chính sự chỉn chu từ những chi tiết nhỏ như vậy, theo mình, mới là điều khiến một website mang lại cảm giác khác biệt. 

3.3 Tìm cảm hứng

Mình sẽ kết bài bằng một mẹo mà khi bạn áp dụng sẽ thấy rõ ngay sự thay đổi trong khả năng thiết kế của AI. 

Đó là cho AI thấy những thiết kế mà bạn muốn nó bắt chước. 

Nếu bạn muốn tạo portfolio cá nhân, bạn có thể vào trang pafolio để xem những website rất đẹp mà người khác đã tạo. Muốn tạo website cho thương hiệu thì có trang awwards, dribble. Muốn thiết kế UI cho app (mobile và web) thì có trang mobbin. 

Chỉ cần screenshot các trang bạn muốn rồi đưa vào coding agents, hoặc chắc ăn hơn nữa thì cho Agent thấy code html của trang bạn muốn bắt chước. Bắt đầu với template có sẵn luôn tiện hơn là thiết kế từ đầu. Đặc biệt là đối với những bạn không có background design giống mình. 

…

Đó cũng là mẹo cuối mình muốn chia sẻ cho các bạn. Thú thật mình không có nhiều tips and tricks, càng không bao giờ dám nhận là chuyên gia.  Chỉ là mình làm nhiều, sai nhiều, và mỗi lần sai thì mình luôn cố gắng học hỏi. 

Mình biết rằng:

Ai giúp ta tạo sản phẩm nhanh hơn, nhưng tạo ra “rác” hay tạo ra sản phẩm khiến người dùng “ngơ ngác”, chỉ có bạn mới quyết định được.