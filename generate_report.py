#!/usr/bin/env python3
"""生成白胡子 vs 赤犬实力对比分析报告"""

from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
import os


def add_table(doc, headers, rows, col_widths=None):
    table = doc.add_table(rows=1 + len(rows), cols=len(headers), style='Light Grid Accent 1')
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(headers):
        cell = table.cell(0, i)
        cell.text = h
        for para in cell.paragraphs:
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for run in para.runs:
                run.bold = True
    for ri, row in enumerate(rows):
        for ci, val in enumerate(row):
            table.cell(ri + 1, ci).text = str(val)
    if col_widths:
        for i, w in enumerate(col_widths):
            for row in table.rows:
                row.cells[i].width = Cm(w)
    return table


def create_report():
    doc = Document()

    style = doc.styles['Normal']
    style.font.name = '微软雅黑'
    style.font.size = Pt(11)
    style.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')
    for level in range(1, 5):
        hs = doc.styles[f'Heading {level}']
        hs.font.color.rgb = RGBColor(0x1a, 0x1a, 0x2e)
        hs.element.rPr.rFonts.set(qn('w:eastAsia'), '微软雅黑')

    section = doc.sections[0]
    section.top_margin = Cm(2.5)
    section.bottom_margin = Cm(2.5)
    section.left_margin = Cm(2.5)
    section.right_margin = Cm(2.5)

    # ═══════ 封面 ═══════
    for _ in range(5):
        doc.add_paragraph()
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = title.add_run('海贼王 Two Piece')
    run.bold = True; run.font.size = Pt(28)
    run.font.color.rgb = RGBColor(0x1a, 0x1a, 0x2e)

    subtitle = doc.add_paragraph()
    subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = subtitle.add_run('白胡子 vs 赤犬 · 全面实力对比分析报告')
    run.bold = True; run.font.size = Pt(18)
    run.font.color.rgb = RGBColor(0xCC, 0x00, 0x00)

    doc.add_paragraph()
    line = doc.add_paragraph()
    line.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = line.add_run('━' * 40)
    run.font.color.rgb = RGBColor(0xCC, 0x00, 0x00)
    doc.add_paragraph()

    info = doc.add_paragraph()
    info.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = info.add_run('分析日期：2026-07-13')
    run.font.size = Pt(12)
    run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)
    doc.add_page_break()

    # ═══════ 核心结论 ═══════
    doc.add_heading('核心结论：白胡子（巅峰期）> 赤犬 > 白胡子（顶上战争期）', level=1)

    doc.add_paragraph(
        '经过对两人在漫画原作中的全部表现、设定集数据、以及作者尾田荣一郎的访谈内容进行综合分析，'
        '结论如下：\n\n'
        '■ 如果以巅峰期（罗杰时代的"世界最强男人"）为参照，白胡子远强于赤犬。'
        '巅峰白胡子是与海贼王罗杰齐名的传说级海贼，其实力足以毁灭世界，'
        '被官方设定为"世界上最强的男人"，拥有毁灭世界的力量。\n\n'
        '■ 如果以顶上战争时期（74岁带病参战）的白胡子为参照，赤犬在正面战斗中占据上风。'
        '顶上战争中白胡子已身患重病、全身插满输液管，无法使用武装色霸气，'
        '反应速度和力量均大幅下降。即便如此，白胡子仍然重伤了赤犬，'
        '将其打得吐血陷入地底裂缝。\n\n'
        '■ 综合来看，"白胡子"的名号包含两个状态——巅峰期和顶上战争期。'
        '巅峰白胡子碾压赤犬，而顶上战争白胡子略逊于赤犬。但考虑到白胡子是在'
        '身负重伤（被斯库亚德刺穿）、重病缠身、无法使用霸气的极端不利条件下作战，'
        '如果双方都处于公平状态，白胡子的实力应当在赤犬之上。'
    )

    doc.add_page_break()

    # ═══════ 一、基本资料对比 ═══════
    doc.add_heading('一、基本资料对比', level=1)
    add_table(doc,
        ['项目', '白胡子（爱德华·纽盖特）', '赤犬（萨卡斯基）'],
        [
            ['称号', '世界最强的男人', '海军元帅（原大将）'],
            ['悬赏金', '50亿4640万贝利', '不适用（海军）'],
            ['恶魔果实', '震震果实（超人系）', '岩浆果实（自然系）'],
            ['霸气', '霸王色·武装色·见闻色', '武装色·见闻色（无霸王色）'],
            ['巅峰年龄', '约40-50岁', '约55岁（顶上战争时）'],
            ['身高', '666cm', '306cm'],
            ['所属', '白胡子海贼团（船长）', '海军本部（大将/元帅）'],
            ['声名', '与罗杰齐名的传说海贼', '绝对正义的海军最高战力'],
        ],
        col_widths=[3, 6, 6]
    )

    doc.add_paragraph()

    # ═══════ 二、恶魔果实能力对比 ═══════
    doc.add_heading('二、恶魔果实能力对比', level=1)

    doc.add_heading('2.1 震震果实 vs 岩浆果实', level=2)
    add_table(doc,
        ['维度', '震震果实（白胡子）', '岩浆果实（赤犬）'],
        [
            ['果实类型', '超人系', '自然系'],
            ['能力本质', '震动一切物质和空间', '产生和控制岩浆'],
            ['攻击范围', '全球级（引发海啸、地震）', '岛屿级（流星火山）'],
            ['破坏力评级', 'SSS（被认为拥有毁灭世界的力量）', 'SS（最高攻击力的自然系）'],
            ['物理伤害', '冲击波、空间裂缝、海啸', '岩浆拳、岩浆弹、熔化万物'],
            ['附加效果', '引发海啸、地裂、大气震动', '高温熔化、持续灼烧伤害'],
            ['元素化免疫', '否（超人系）', '是（自然系，可免疫物理攻击）'],
        ],
        col_widths=[3, 6, 6]
    )

    doc.add_heading('2.2 能力克制分析', level=2)
    doc.add_paragraph(
        '岩浆果实被官方设定为"自然系中最高攻击力"，但震震果实的破坏力在设定上是'
        '"足以毁灭世界"的级别。从破坏力上限来看，震震果实远高于岩浆果实。'
        '白胡子在顶上战争中一拳震裂马林梵多的整个海湾，随手引发数十米高的海啸，'
        '甚至将海军本部的大气层都震出裂缝——这是赤犬的岩浆能力无法企及的破坏规模。\n\n'
        '然而，岩浆果实的元素化特性为赤犬提供了额外的防御优势。'
        '白胡子的物理攻击（如薙刀砍击）无法直接命中赤犬的本体，'
        '必须使用武装色霸气才能触碰到自然系能力者。而顶上战争时期的白胡子'
        '由于重病和年龄原因，霸气使用极为有限。'
    )

    doc.add_paragraph()

    # ═══════ 三、霸气能力对比 ═══════
    doc.add_heading('三、霸气能力对比', level=1)
    add_table(doc,
        ['霸气类型', '白胡子', '赤犬'],
        [
            ['霸王色霸气', '✅ 拥有（顶级水准）', '❌ 未展现'],
            ['武装色霸气', '✅ 拥有（巅峰期顶级）', '✅ 拥有（大将级）'],
            ['见闻色霸气', '✅ 拥有', '✅ 拥有（大将级）'],
        ],
        col_widths=[4, 5.5, 5.5]
    )

    doc.add_paragraph(
        '霸王色霸气是决定性差距之一。白胡子拥有顶级的霸王色霸气，'
        '这是"王者资质"的证明，全球仅有极少数人能拥有。赤犬虽然实力强大，'
        '但从未展现过霸王色霸气。霸王色霸气不仅可以威吓杂兵，'
        '在高端对战中还可以缠绕在攻击上大幅提升威力。\n\n'
        '值得注意的是，顶上战争中的白胡子由于身体条件限制，'
        '几乎无法有效使用霸气，这是他在战斗中处于下风的关键原因之一。'
        '巅峰白胡子若能够充分发挥三色霸气+震震果实的能力组合，'
        '其实力将远超赤犬。'
    )

    doc.add_page_break()

    # ═══════ 四、战斗实绩对比 ═══════
    doc.add_heading('四、战斗实绩对比', level=1)

    doc.add_heading('4.1 顶上战争正面交锋', level=2)
    doc.add_paragraph(
        '白胡子和赤犬在顶上战争中有两次直接交手：\n\n'
        '第一次交锋：白胡子在重伤状态下（被斯库亚德刺穿胸膛）从背后突袭赤犬，'
        '一拳将其击倒并打入地底裂缝。赤犬被打得口吐鲜血，一度失去战斗能力。'
        '这是整个顶上战争中海军大将受到的最严重伤害。\n\n'
        '第二次交锋：赤犬从地底钻出后，趁白胡子不备，用岩浆拳打穿白胡子的胸膛，'
        '并烧毁了白胡子半张脸。白胡子在受到致命伤后，仍然用最后一击将赤犬'
        '再次击飞，并将海军本部震裂。随后白胡子站立而亡，背部没有一处伤口。'
    )

    doc.add_heading('4.2 主要战绩对比', level=2)
    add_table(doc,
        ['对手/事件', '白胡子的战绩', '赤犬的战绩'],
        [
            ['对战罗杰', '多次交战，不分胜负（巅峰期）', '未交手'],
            ['对战金狮子', '击败金狮子舰队', '未交手'],
            ['对战战国/卡普', '多次交战，不分胜负', '同僚关系'],
            ['对战白胡子（顶上）', '—', '重伤白胡子（但白胡子已濒死）'],
            ['对战艾斯', '—', '击杀艾斯'],
            ['对战青雉', '—', '激战10天获胜，晋升元帅'],
            ['对战路飞', '照顾并保护', '追杀，几乎击杀'],
            ['对战马尔科等队长', '—', '压制全体队长'],
            ['对战国/香克斯', '与香克斯把酒言欢', '被香克斯一剑挡下攻击'],
        ],
        col_widths=[4.5, 5, 5.5]
    )

    doc.add_paragraph()

    # ═══════ 五、综合实力维度评分 ═══════
    doc.add_heading('五、综合实力维度评分', level=1)
    doc.add_paragraph('评分标准：满分 10 分，以巅峰状态为参照。括号内为顶上战争时期评分。')

    add_table(doc,
        ['维度', '白胡子', '赤犬', '优势方'],
        [
            ['攻击力', '10（8）', '9', '白胡子（巅峰）'],
            ['防御力', '9（6）', '8', '白胡子（巅峰）'],
            ['速度/反应', '8（4）', '9', '赤犬'],
            ['耐力/续航', '9（5）', '9', '持平'],
            ['果实开发', '10（8）', '9', '白胡子（巅峰）'],
            ['霸气强度', '10（5）', '8', '白胡子（巅峰）'],
            ['战斗经验', '10', '9', '白胡子'],
            ['破坏范围', '10（9）', '8', '白胡子'],
            ['战略头脑', '8', '9', '赤犬'],
            ['意志力', '10', '9', '白胡子'],
            ['综合得分', '94（67）', '87', '白胡子（巅峰）'],
        ],
        col_widths=[3.5, 3, 3, 4.5]
    )

    doc.add_paragraph()
    doc.add_paragraph(
        '从综合得分可以看出：巅峰白胡子 94 分 > 赤犬 87 分 > 顶上白胡子 67 分。'
        '赤犬虽然在顶上战争中击败了白胡子，但击败的是一个实力仅剩巅峰期 70% 左右的'
        '重病老人。如果两人都处于巅峰状态，白胡子的胜算在八成以上。'
    )

    doc.add_page_break()

    # ═══════ 六、决定性因素分析 ═══════
    doc.add_heading('六、决定性因素分析', level=1)

    doc.add_heading('6.1 白胡子占优势的因素', level=2)
    factors = [
        ('破坏力上限', '震震果实拥有毁灭世界的力量，这是海贼王世界中最高级别的破坏力描述。'
         '赤犬的岩浆果实虽然攻击力在自然系中顶尖，但其破坏规模上限无法与震震果实相比。'),
        ('霸王色霸气', '白胡子拥有顶级霸王色霸气，这是赤犬所不具备的。霸王色缠绕可以将攻击力'
         '提升到另一个层次，巅峰白胡子的攻击配上霸王色缠绕，赤犬难以正面抵挡。'),
        ('战斗经验', '白胡子从青年时期起就是世界顶级海贼，与罗杰、金狮子等传说级人物多次交手，'
         '战斗经验比赤犬丰富数十年。'),
        ('身体素质', '巅峰白胡子的身体素质是怪物级的，666cm的巨人般体格赋予了他在力量上的绝对优势。'),
        ('领袖魅力', '白胡子拥有让所有船员心甘情愿称为"老爹"的人格魅力，这种意志力在战斗中转化为'
         '不屈不挠的战斗意志，即使身受重伤也绝不倒下。'),
    ]
    for title, desc in factors:
        p = doc.add_paragraph()
        run = p.add_run(f'• {title}：')
        run.bold = True
        p.add_run(desc)

    doc.add_heading('6.2 赤犬占优势的因素', level=2)
    factors = [
        ('元素化防御', '自然系岩浆果实的元素化特性让赤犬在面对非霸气攻击时完全免疫。'
         '顶上战争中白胡子因无法有效使用霸气，多数攻击无法直接命中赤犬本体。'),
        ('果实属性优势', '岩浆果实被官方设定为"自然系中最高攻击力"，其高温属性可以对绝大多数'
         '对手造成持续的灼烧伤害，且烧伤难以愈合。'),
        ('战斗状态', '顶上战争时的赤犬处于巅峰年龄和全盛状态，而白胡子已经74岁高龄且重病缠身。'
         '年轻和健康是战斗中不可忽视的优势。'),
        ('战术思维', '赤犬在战斗中善于利用策略（如利用斯库亚德刺杀白胡子），'
         '而白胡子更倾向于正面碾压。'),
    ]
    for title, desc in factors:
        p = doc.add_paragraph()
        run = p.add_run(f'• {title}：')
        run.bold = True
        p.add_run(desc)

    doc.add_paragraph()

    # ═══════ 七、不同场景推演 ═══════
    doc.add_heading('七、不同场景战斗推演', level=1)

    doc.add_heading('场景一：巅峰白胡子 vs 赤犬', level=2)
    doc.add_paragraph(
        '巅峰白胡子（40-50岁）拥有完整的武装色、见闻色和霸王色霸气，震震果实能力全开。'
        '赤犬的岩浆攻击无法击破白胡子覆盖了武装色霸气的身体，'
        '而白胡子的震震拳配上霸王色缠绕可以轻易突破赤犬的元素化防御。'
        '战斗结果：白胡子胜率 85%，赤犬胜率 15%。'
    )

    doc.add_heading('场景二：顶上战争白胡子 vs 赤犬（实际战况）', level=2)
    doc.add_paragraph(
        '74岁重病白胡子无法使用霸气，身体反应迟钝，且已受致命伤。'
        '赤犬利用元素化免疫了绝大部分物理攻击，用岩浆果实的高温优势持续消耗。'
        '但即使如此，白胡子仍然两次将赤犬击倒，最后一次更是让赤犬在数分钟内无法起身。'
        '战斗结果：赤犬胜（但属于惨胜，若非白胡子先被斯库亚德刺伤，结果可能不同）。'
    )

    doc.add_heading('场景三：公平对决（同状态、无干扰）', level=2)
    doc.add_paragraph(
        '假设两人都处于同等状态（年龄相同、健康相同、无第三方干扰），'
        '那么白胡子的三色霸气+震震果实的组合将全面压制赤犬的岩浆果实。'
        '特别是白胡子的霸王色缠绕——这是连四皇都极为倚重的顶级战斗技能——'
        '赤犬没有相应的手段来对抗。'
        '战斗结果：白胡子胜率 75%，赤犬胜率 25%。'
    )

    doc.add_page_break()

    # ═══════ 八、结论与评级 ═══════
    doc.add_heading('八、最终评级', level=1)

    add_table(doc,
        ['级别', '定义', '代表人物', '战力范围'],
        [
            ['SSS+', '传说级（海贼王级别）', '罗杰、巅峰白胡子', '10万+'],
            ['SSS', '传说级门槛', '战国、卡普（巅峰）', '9-10万'],
            ['SS', '四皇/元帅级', '赤犬、凯多、大妈、香克斯', '7-9万'],
            ['S+', '顶级大将/皇副级', '青雉、黄猿、贝克曼', '5-7万'],
        ],
        col_widths=[2, 4.5, 5, 3]
    )

    doc.add_paragraph()
    doc.add_paragraph(
        '■ 巅峰白胡子：SSS+ 级。与罗杰并列的传说级，拥有毁灭世界的力量，'
        '是官方认证的"世界最强的男人"。\n\n'
        '■ 顶上战争白胡子：SS 级。虽然实力大幅下降，但依然能压制海军大将，'
        '只是面对赤犬时因无法使用霸气和身体重伤而落败。\n\n'
        '■ 赤犬：SS 级。海军最高战力，击败青雉晋升元帅，'
        '攻击力在自然系中首屈一指。但他的实力上限被没有霸王色霸气所限制。\n\n'
        '■ 最终结论：白胡子（巅峰期）> 赤犬 > 白胡子（顶上战争期）。'
        '"世界上最强的男人"的名号当之无愧，即使在 74 岁高龄带病上阵，'
        '仍然能重创海军最高战力——如果他处于巅峰状态，'
        '赤犬不会有一丝胜算。'
    )

    doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run('━' * 40)
    run.font.color.rgb = RGBColor(0xCC, 0xCC, 0xCC)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run('报告生成日期：2026-07-13')
    run.font.size = Pt(10)
    run.font.color.rgb = RGBColor(0x99, 0x99, 0x99)

    # ── 保存 ──
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, 'static', '白胡子vs赤犬实力对比分析报告.docx')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc.save(output_path)
    print(f'报告已生成：{output_path}')
    print(f'文件大小：{os.path.getsize(output_path) / 1024:.1f} KB')
    return output_path


if __name__ == '__main__':
    create_report()
