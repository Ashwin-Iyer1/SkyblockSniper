package ashwiniyer06.gmail.com;
import net.minecraft.client.Minecraft;
import net.minecraft.command.CommandBase;
import net.minecraft.command.CommandException;
import net.minecraft.command.ICommandSender;
import net.minecraft.entity.Entity;
import net.minecraft.entity.player.EntityPlayer;
import net.minecraft.util.ChatComponentText;
import net.minecraft.util.ChatComponentTranslation;
import net.minecraftforge.event.terraingen.OreGenEvent;

import java.util.Collections;
import java.util.Comparator;
import java.util.List;
import java.util.Objects;

public class FlipStart extends CommandBase{
    private AHFlip ahFlipInstance;
    public FlipStart(AHFlip ahFlipInstance) {
        this.ahFlipInstance = ahFlipInstance;
    }

    @Override
    public String getCommandName() {
        return "Flip";
    }

    @Override
    public String getCommandUsage(ICommandSender sender) {
        return "";
    }
    boolean check = false;
    String Prev_flip = "";
    @Override
    public void processCommand(ICommandSender sender, String[] args) throws CommandException {
        check = !check;
        if (sender instanceof EntityPlayer) {
            EntityPlayer player = (EntityPlayer) sender;
            if (args.length > 0) {
                String flipKeyword = args[0].toLowerCase(); // Convert to lowercase for case-insensitivity
                player.addChatComponentMessage(new ChatComponentText("Flip Started with keyword: " + flipKeyword));

                ahFlipInstance.startFlipping(flipKeyword);
//            } else {
//                player.addChatComponentMessage(new ChatComponentText("Auto Flip " + (check ? "Started":"Stopped")));
//                new Thread(() -> {
//                    while(check){
//                        try {
//                            String best_flip = AHFlip.getBestAuction().replaceAll("\"", "");
//                            if(!Objects.equals(Prev_flip, best_flip)){
//                                ahFlipInstance.startFlipping(best_flip);
//                                System.out.println(best_flip);
//                                Prev_flip = best_flip;
//                            }
//                        } catch (Exception e) {
//                            throw new RuntimeException(e);
//                        }
//                        try {
//                            Thread.sleep(1000);
//                        } catch (InterruptedException e) {
//                            throw new RuntimeException(e);
//                        }
//                    }
//                }).start();
            }
        }


    }
    @Override
    public int getRequiredPermissionLevel() {
        return 0;
    }

}
