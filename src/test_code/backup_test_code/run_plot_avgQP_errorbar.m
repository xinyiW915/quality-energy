
x264_data = readtable('../metrics/YOUTUBE_UGC_1080P_all_average_Animation_x264_metrics.csv');
x265_data = readtable('../metrics/YOUTUBE_UGC_1080P_all_average_Animation_x265_metrics.csv');
VP9_data = readtable('../metrics/YOUTUBE_UGC_1080P_all_average_Animation_VP9_metrics');
SVT_AV1_data = readtable('../metrics/YOUTUBE_UGC_1080P_all_average_Animation_SVT-AV1_metrics.csv');

x1 = table2array(x264_data(: ,"Bitrate_kb_s_"));
y1 = table2array(x264_data(: ,"PSNR_dB_"));
x1 = transpose(x1);
y1 = transpose(y1);

err_x1 = table2array(x264_data(: ,"std_bitrate"));
err_y1 = table2array(x264_data(: ,"std_psnr"));
err_x1 = transpose(err_x1);
err_y1 = transpose(err_y1);
yneg = transpose(err_y1);
ypos = transpose(err_y1);
xneg = transpose(err_x1);
xpos = transpose(err_x1);

x2 = table2array(x265_data(: ,"Bitrate_kb_s_"));
y2 = table2array(x265_data(: ,"PSNR_dB_"));
x2 = transpose(x2);
y2 = transpose(y2);

err_x2 = table2array(x265_data(: ,"std_bitrate"));
err_y2 = table2array(x265_data(: ,"std_psnr"));
err_x2 = transpose(err_x2);
err_y2 = transpose(err_y2);

errorbar(x1,y1,yneg,ypos,xneg,xpos,'o')
% e = errorbar(x1,y1,err_y1);
% e.Color = '#1F77B4';
% hold on;
% e = errorbar(x1,y1,err_x1, 'horizontal');
% e.Color = '#1F77B4';
% xlabel('Bitrate (kb/s)');
% ylabel('PSNR (dB)');
% title('PSNR vs Bitrate')
% hold on;
% e = errorbar(x2,y2,err_y2);
% e.Color = '#FF7F0E';
% hold on;
% e = errorbar(x2,y2,err_x2, 'horizontal');
% e.Color = '#FF7F0E';
% xlabel('Bitrate (kb/s)');
% ylabel('PSNR (dB)');
% title('PSNR vs Bitrate')
% h = legend('x264', 'x265');
% set(h,'FontSize',12, 'Location','southeast');

% ax = gca;
% exportgraphics(ax,'error_bar.png','Resolution',600)