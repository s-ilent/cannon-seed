.set noat      /* allow manual use of $at */
.set noreorder /* don't insert nops after branches */

nonmatching GetVideoMode, 0x10

glabel GetVideoMode
    /* 48194 80067994 0B80023C */  lui        $v0, %hi(video_mode)
    /* 48198 80067998 7044428C */  lw         $v0, %lo(video_mode)($v0)
    /* 4819C 8006799C 0800E003 */  jr         $ra
    /* 481A0 800679A0 00000000 */   nop
endlabel GetVideoMode
