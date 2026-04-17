`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 11/13/2025 09:50:10 PM
// Design Name: 
// Module Name: top
// Project Name: 
// Target Devices: 
// Tool Versions: 
// Description: 
// 
// Dependencies: 
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// 
//////////////////////////////////////////////////////////////////////////////////

module UART_RX_To_7_Seg_Top (
    input  logic        i_Clock,
    input  logic        i_RX_Serial,
    output logic        o_TX_Serial,

    output logic [6:0]  seg,
    output logic [7:0]  an,
    output logic        dp,

    output logic        LED0,

    output logic [3:0]  vgaRed,
    output logic [3:0]  vgaGreen,
    output logic [3:0]  vgaBlue,
    output logic        Hsync,
    output logic        Vsync
);

    // ============================================================
    // Power-on reset
    // ============================================================
    localparam int CLKS_PER_BIT = 868;

    logic [23:0] por_cnt = 24'd0;
    logic        reset   = 1'b1;

    always_ff @(posedge i_Clock) begin
        if (por_cnt != 24'hFFFFFF) begin
            por_cnt <= por_cnt + 24'd1;
            reset   <= 1'b1;
        end else begin
            reset   <= 1'b0;
        end
    end

    // ============================================================
    // Clock Wizard (100 MHz → 25 MHz)
    // ============================================================
    logic clk_25, clk_locked;

    clk_wiz_0 u_clk_wiz (
        .clk_in1  (i_Clock),
        .reset    (reset),
        .clk_out1 (clk_25),
        .locked   (clk_locked)
    );

    logic reset_25;
    assign reset_25 = reset | ~clk_locked;

    // ============================================================
    // UART RX
    // ============================================================
    logic       rx_dv;
    logic [7:0] rx_byte;

    UART_RX #(.CLKS_PER_BIT(CLKS_PER_BIT)) u_uart_rx (
        .i_Clock     (i_Clock),
        .i_RX_Serial (i_RX_Serial),
        .o_RX_DV     (rx_dv),
        .o_RX_Byte   (rx_byte)
    );

    // ============================================================
    // UART TX (loopback)
    // ============================================================
    logic tx_dv, tx_active, tx_done;
    logic [7:0] tx_byte;

    always_ff @(posedge i_Clock) begin
        if (reset) begin
            tx_dv   <= 0;
            tx_byte <= 0;
        end else begin
            tx_dv <= 0;
            if (rx_dv && !tx_active) begin
                tx_byte <= rx_byte;
                tx_dv   <= 1;
            end
        end
    end

    UART_TX #(.CLKS_PER_BIT(CLKS_PER_BIT)) u_uart_tx (
        .i_Clock     (i_Clock),
        .i_TX_DV     (tx_dv),
        .i_TX_Byte   (tx_byte),
        .o_TX_Active (tx_active),
        .o_TX_Serial (o_TX_Serial),
        .o_TX_Done   (tx_done)
    );

    // ============================================================
    // EEG Parser
    // ============================================================
    logic        packet_valid;
    logic [15:0] alpha, beta, theta, delta;

    EEG_Packet_Parser u_parser (
        .i_Clock        (i_Clock),
        .i_Reset        (reset),
        .i_Rx_DV        (rx_dv),
        .i_Rx_Byte      (rx_byte),
        .o_Packet_Valid (packet_valid),
        .o_Alpha        (alpha),
        .o_Beta         (beta),
        .o_Theta        (theta),
        .o_Delta        (delta)
    );

    // ============================================================
    // LED activity indicator
    // ============================================================
    logic [22:0] led_cnt;

    always_ff @(posedge i_Clock) begin
        if (reset) begin
            led_cnt <= 0;
        end else begin
            if (packet_valid)
                led_cnt <= 23'd1_000_000;
            else if (led_cnt != 0)
                led_cnt <= led_cnt - 1;
        end
    end

    assign LED0 = (led_cnt != 0);

    // ============================================================
    // 7-seg display (alpha)
    // ============================================================
    logic [7:0] display_byte_r;

    always_ff @(posedge i_Clock) begin
        if (reset)
            display_byte_r <= 0;
        else if (packet_valid)
            display_byte_r <= alpha[7:0];
    end

    SevenSeg_2Digit_Mux u_disp (
        .i_Clock (i_Clock),
        .i_Reset (reset),
        .i_Byte  (display_byte_r),
        .seg     (seg),
        .an      (an),
        .dp      (dp)
    );

    // ============================================================
    // EEG → Fractal Mapping (RE-ENABLED, CLEANED)
    // ============================================================

    localparam logic signed [31:0] Q28_ONE  = 32'sh1000_0000;
    localparam logic signed [31:0] Q28_HALF = 32'sh0800_0000;

    localparam logic signed [31:0] BASE_CENTER_RE = -32'sh0C00_0000; // -0.75
    localparam logic signed [31:0] BASE_CENTER_IM =  32'sh0000_0000;

    logic signed [31:0] inv_zoom_q28_100;
    logic signed [31:0] center_re_q28_100;
    logic signed [31:0] center_im_q28_100;
    logic [15:0]        iter_limit_100;
    logic [7:0]         palette_id_100;

    logic signed [16:0] theta_centered;
    logic signed [16:0] delta_centered;

    always_comb begin
        theta_centered = $signed({1'b0, theta}) - 17'sd32768;
        delta_centered = $signed({1'b0, delta}) - 17'sd32768;
    end

    always_ff @(posedge i_Clock) begin
        if (reset) begin
            inv_zoom_q28_100  <= Q28_ONE;
            center_re_q28_100 <= BASE_CENTER_RE;
            center_im_q28_100 <= BASE_CENTER_IM;
            iter_limit_100    <= 16'd120;
            palette_id_100    <= 0;
        end else if (packet_valid) begin

            // Smooth inverse zoom from 1.0 down to ~0.5
            // alpha = 0      -> inv_zoom = 1.0
            // alpha = 65535  -> inv_zoom ≈ 0.5
            inv_zoom_q28_100 <= Q28_ONE - ({16'd0, alpha} >>> 1);

            // -------------------------------
            // SMALL center movement (fixed)
            // -------------------------------
            center_re_q28_100 <= BASE_CENTER_RE + (theta_centered <<< 10);
            center_im_q28_100 <= BASE_CENTER_IM + (delta_centered <<< 10);

            // -------------------------------
            // iteration range (safe)
            // -------------------------------
            iter_limit_100 <= 16'd80 + {8'd0, beta[15:9]};

            // -------------------------------
            // palette (few options)
            // -------------------------------
            palette_id_100 <= alpha[15:14];

        end
    end

    // ============================================================
    // Clock domain crossing
    // ============================================================
    logic signed [31:0] inv_zoom_q28_25_d1,  inv_zoom_q28_25;
    logic signed [31:0] center_re_q28_25_d1, center_re_q28_25;
    logic signed [31:0] center_im_q28_25_d1, center_im_q28_25;
    logic [15:0]        iter_limit_25_d1,    iter_limit_25;
    logic [7:0]         palette_id_25_d1,    palette_id_25;

    always_ff @(posedge clk_25 or posedge reset_25) begin
        if (reset_25) begin
            inv_zoom_q28_25_d1  <= Q28_ONE;
            inv_zoom_q28_25     <= Q28_ONE;
            center_re_q28_25_d1 <= BASE_CENTER_RE;
            center_re_q28_25    <= BASE_CENTER_RE;
            center_im_q28_25_d1 <= BASE_CENTER_IM;
            center_im_q28_25    <= BASE_CENTER_IM;
            iter_limit_25_d1    <= 120;
            iter_limit_25       <= 120;
            palette_id_25_d1    <= 0;
            palette_id_25       <= 0;
        end else begin
            inv_zoom_q28_25_d1  <= inv_zoom_q28_100;
            inv_zoom_q28_25     <= inv_zoom_q28_25_d1;

            center_re_q28_25_d1 <= center_re_q28_100;
            center_re_q28_25    <= center_re_q28_25_d1;

            center_im_q28_25_d1 <= center_im_q28_100;
            center_im_q28_25    <= center_im_q28_25_d1;

            iter_limit_25_d1    <= iter_limit_100;
            iter_limit_25       <= iter_limit_25_d1;

            palette_id_25_d1    <= palette_id_100;
            palette_id_25       <= palette_id_25_d1;
        end
    end

    // ============================================================
    // VGA + Fractal Renderer
    // ============================================================
    logic vga_active;
    logic [9:0] vga_x, vga_y;
    logic vga_hsync_raw, vga_vsync_raw;

    VGA_640x480_Timing u_vga_timing (
        .i_Clock  (clk_25),
        .i_Reset  (reset_25),
        .o_HSync  (vga_hsync_raw),
        .o_VSync  (vga_vsync_raw),
        .o_X      (vga_x),
        .o_Y      (vga_y),
        .o_Active (vga_active)
    );

    assign Hsync = vga_hsync_raw;
    assign Vsync = vga_vsync_raw;

    fractal_lowres_renderer u_renderer (
        .clk           (clk_25),
        .rst_n         (~reset_25),
        .px_x          (vga_x),
        .px_y          (vga_y),
        .px_active     (vga_active),
        .inv_zoom_q28  (inv_zoom_q28_25),
        .center_re_q28 (center_re_q28_25),
        .center_im_q28 (center_im_q28_25),
        .iter_limit    (iter_limit_25),
        .palette_id    (palette_id_25),
        .out_red       (vgaRed),
        .out_green     (vgaGreen),
        .out_blue      (vgaBlue)
    );

endmodule