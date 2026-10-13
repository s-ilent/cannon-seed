.set noat      /* allow manual use of $at */
.set noreorder /* don't insert nops after branches */

nonmatching SetVideoMode, 0x18

glabel SetVideoMode
    /* 110E4 800308E4 0580023C */  lui        $v0, %hi(video_mode)
    /* 110E8 800308E8 20CF428C */  lw         $v0, %lo(video_mode)($v0)
    /* 110EC 800308EC 0580013C */  lui        $at, %hi(video_mode)
    /* 110F0 800308F0 20CF24AC */  sw         $a0, %lo(video_mode)($at)
    /* 110F4 800308F4 0800E003 */  jr         $ra
    /* 110F8 800308F8 00000000 */   nop
endlabel SetVideoMode
