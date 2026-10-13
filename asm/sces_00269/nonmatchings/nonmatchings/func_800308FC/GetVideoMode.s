.set noat      /* allow manual use of $at */
.set noreorder /* don't insert nops after branches */

nonmatching GetVideoMode, 0x10

glabel GetVideoMode
    /* 110FC 800308FC 0580023C */  lui        $v0, %hi(video_mode)
    /* 11100 80030900 20CF428C */  lw         $v0, %lo(video_mode)($v0)
    /* 11104 80030904 0800E003 */  jr         $ra
    /* 11108 80030908 00000000 */   nop
endlabel GetVideoMode
